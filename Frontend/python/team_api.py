import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

APP = FastAPI(title="HRM Team Formation ML API", version="1.0.0")
APP.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "team_config.json"
LOCAL_EMPLOYEE_CSV = BASE_DIR / "employees.csv"
EMPLOYEE_API_URL = "http://localhost:8080/api/employees"

DEFAULT_CONFIG = {
    "minClusters": 2,
    "maxClusters": 8,
    "randomState": 42,
    "kmeansNInit": 20,
    "scoreWeights": {
        "skillSimilarity": 0.5,
        "experience": 0.3,
        "salaryFit": 0.2,
    },
}


class TeamConfigRequest(BaseModel):
    scoreWeights: dict[str, float] | None = None
    minClusters: int | None = None
    maxClusters: int | None = None
    randomState: int | None = None
    kmeansNInit: int | None = None


class TeamGenerateRequest(BaseModel):
    criteria: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)


def read_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG


def write_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def split_skills(skills_raw):
    if not skills_raw:
        return []
    if isinstance(skills_raw, list):
        return [str(s).strip().lower() for s in skills_raw if str(s).strip()]
    text = str(skills_raw).replace("|", ",").replace(";", ",")
    return [s.strip().lower() for s in text.split(",") if s.strip()]


def cosine_similarity(a, b):
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def availability_score(raw):
    mapping = {
        "available": 1.0,
        "busy": 0.6,
        "on leave": 0.1,
        "unavailable": 0.0,
    }
    return mapping.get(str(raw or "").strip().lower(), 0.5)


def normalize(values, default=0.0):
    arr = np.array(values, dtype=float)
    if len(arr) == 0:
        return arr
    min_v = float(np.min(arr))
    max_v = float(np.max(arr))
    if math.isclose(min_v, max_v):
        return np.full_like(arr, default if default > 0 else 1.0)
    return (arr - min_v) / (max_v - min_v)


def fetch_employees():
    try:
        response = requests.get(EMPLOYEE_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError("Employees API returned invalid response.")
        if len(data) > 0:
            return data
    except Exception:
        pass

    return load_employees_from_local_csv()


def parse_experience_from_start_date(value):
    if not value:
        return 0.0
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            start = datetime.strptime(str(value).strip(), fmt)
            years = max(0, datetime.now().year - start.year)
            return float(years)
        except ValueError:
            continue
    return 0.0


def load_employees_from_local_csv():
    if not LOCAL_EMPLOYEE_CSV.exists():
        raise FileNotFoundError(
            "No employee source available. Start employee backend on :8080 or keep python/employees.csv."
        )

    employees = []
    with open(LOCAL_EMPLOYEE_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            team = (row.get("Team") or "General").strip() or "General"
            name = (row.get("First Name") or f"Candidate {i + 1}").strip()
            salary = float(row.get("Salary") or 0)
            bonus = float(row.get("Bonus %") or 0)
            experience = parse_experience_from_start_date(row.get("Start Date"))
            senior_raw = str(row.get("Senior Management") or "").strip().lower()
            is_senior = senior_raw == "true"

            skills = [team.lower()]
            if team.lower() in {"marketing", "finance"}:
                skills.extend(["analytics", "communication"])
            elif team.lower() in {"engineering", "it", "development"}:
                skills.extend(["backend", "testing", "devops"])
            else:
                skills.extend(["problem solving", "collaboration"])

            role = f"{team} Specialist"
            if is_senior:
                role = f"Senior {team} Lead"
                skills.append("leadership")

            skill_level = max(1, min(10, int(round((bonus / 2.0) + 3))))
            performance = max(0.0, min(10.0, round(bonus / 2.0, 2)))

            employees.append(
                {
                    "id": f"csv_{i + 1}",
                    "employeeId": f"CSV{i + 1:04d}",
                    "name": name,
                    "department": team,
                    "role": role,
                    "skills": ", ".join(dict.fromkeys(skills)),
                    "skillLevel": skill_level,
                    "experience": experience,
                    "category": "Full-time",
                    "availability": "Available",
                    "performanceRating": performance,
                    "salary": salary,
                    "status": "Present",
                }
            )

    return employees


def select_kmeans_k(feature_matrix, min_k, max_k, random_state, n_init):
    n_samples = feature_matrix.shape[0]
    if n_samples < 3:
        return 1

    lower = max(2, min_k)
    upper = min(max_k, n_samples - 1)
    if lower > upper:
        return 2 if n_samples >= 2 else 1

    best_k = lower
    best_score = -1.0

    for k in range(lower, upper + 1):
        model = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        labels = model.fit_predict(feature_matrix)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(feature_matrix, labels)
        if score > best_score:
            best_score = score
            best_k = k

    return best_k


@APP.get("/api/team/config")
def get_config():
    return read_config()


@APP.post("/api/team/config")
def save_config(payload: TeamConfigRequest):
    payload_dict = payload.model_dump(exclude_none=True)
    merged = {**read_config(), **payload_dict}
    merged["scoreWeights"] = {
        **DEFAULT_CONFIG["scoreWeights"],
        **(payload_dict.get("scoreWeights") or {}),
    }
    write_config(merged)
    return {"success": True, "config": merged}


def _generate_team(payload: dict[str, Any]):
    try:
        criteria = payload.get("criteria") or {}
        config = {**read_config(), **(payload.get("config") or {})}
        config["scoreWeights"] = {**DEFAULT_CONFIG["scoreWeights"], **(config.get("scoreWeights") or {})}

        team_size = int(criteria.get("teamSize") or 4)
        number_of_teams = int(criteria.get("numberOfTeams") or 2)
        if number_of_teams < 1:
            number_of_teams = 1
        primary_skills = split_skills(criteria.get("primarySkills"))
        secondary_skills = split_skills(criteria.get("secondarySkills"))
        all_project_skills = list(dict.fromkeys(primary_skills + secondary_skills))
        min_experience = float(criteria.get("minExperience") or 0)
        required_role = str(criteria.get("requiredRole") or "").strip().lower()

        employees = fetch_employees()
        if not employees:
            raise HTTPException(status_code=400, detail="No employees available.")

        eligible = []
        for emp in employees:
            exp = float(emp.get("experience") or 0)
            availability = str(emp.get("availability") or "Available")
            if availability.lower() in {"on leave", "unavailable"}:
                continue
            if exp < min_experience:
                continue
            if required_role:
                role_text = str(emp.get("role") or "").strip().lower()
                dept_text = str(emp.get("department") or "").strip().lower()
                if required_role not in role_text and required_role not in dept_text:
                    continue
            eligible.append(emp)

        if len(eligible) < 2:
            role_hint = f" for role '{required_role}'" if required_role else ""
            raise HTTPException(
                status_code=400,
                detail=f"Not enough eligible employees{role_hint} to run K-Means.",
            )

        if team_size > len(eligible):
            team_size = len(eligible)

        skill_vocab = all_project_skills[:]
        for emp in eligible:
            for sk in split_skills(emp.get("skills")):
                if sk not in skill_vocab:
                    skill_vocab.append(sk)

        if not skill_vocab:
            skill_vocab = ["general"]

        project_vec = np.zeros(len(skill_vocab))
        for i, sk in enumerate(skill_vocab):
            if sk in primary_skills:
                project_vec[i] = 1.0
            elif sk in secondary_skills:
                project_vec[i] = 0.6
            else:
                project_vec[i] = 0.2

        skill_similarity = []
        feature_rows = []
        salaries = []
        experiences = []

        for emp in eligible:
            emp_skill_vec = np.zeros(len(skill_vocab))
            for sk in split_skills(emp.get("skills")):
                if sk in skill_vocab:
                    emp_skill_vec[skill_vocab.index(sk)] = 1.0

            sim = cosine_similarity(emp_skill_vec, project_vec)
            skill_similarity.append(sim)

            exp = float(emp.get("experience") or 0)
            experiences.append(exp)
            sal = float(emp.get("salary") or 0)
            salaries.append(sal)
            skill_level = float(emp.get("skillLevel") or 1)
            perf = float(emp.get("performanceRating") or 0)
            avail = availability_score(emp.get("availability"))

            feature_rows.append([skill_level, exp, perf, avail, sim])

        feature_matrix = np.array(feature_rows, dtype=float)
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(feature_matrix)

        best_k = select_kmeans_k(
            scaled_features,
            int(config.get("minClusters", 2)),
            int(config.get("maxClusters", 8)),
            int(config.get("randomState", 42)),
            int(config.get("kmeansNInit", 20)),
        )

        kmeans = KMeans(
            n_clusters=best_k,
            random_state=int(config.get("randomState", 42)),
            n_init=int(config.get("kmeansNInit", 20)),
        )
        labels = kmeans.fit_predict(scaled_features)

        cluster_attention = {}
        for cluster_id in np.unique(labels):
            idx = np.where(labels == cluster_id)[0]
            cluster_attention[int(cluster_id)] = float(np.mean(np.array(skill_similarity)[idx]))
        best_cluster = max(cluster_attention, key=cluster_attention.get)

        selected_idx = np.where(labels == best_cluster)[0].tolist()
        if len(selected_idx) < team_size * number_of_teams:
            selected_idx = list(range(len(eligible)))

        exp_norm = normalize(experiences)
        sal_norm = normalize(salaries, default=0.5)
        sim_norm = normalize(skill_similarity)

        w_skill = float(config["scoreWeights"]["skillSimilarity"])
        w_exp = float(config["scoreWeights"]["experience"])
        w_sal = float(config["scoreWeights"]["salaryFit"])

        ranked = []
        for i in selected_idx:
            score = (w_skill * sim_norm[i]) + (w_exp * exp_norm[i]) + (w_sal * sal_norm[i])
            enriched = {
                **eligible[i],
                "matchScore": round(float(score) * 100, 2),
                "clusterId": int(labels[i]),
            }
            ranked.append(enriched)

        ranked.sort(key=lambda x: x["matchScore"], reverse=True)

        # Deduplicate by stable key for dynamic CSV inputs
        unique_ranked = []
        seen_keys = set()
        for row in ranked:
            key = str(row.get("employeeId") or row.get("id") or f"{row.get('name')}-{row.get('role')}").lower()
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique_ranked.append(row)

        if len(unique_ranked) == 0:
            raise HTTPException(
                status_code=400,
                detail="No candidates available after deduplication.",
            )

        total_required = team_size * number_of_teams
        pool = unique_ranked[: min(total_required, len(unique_ranked))]

        # Build teams dynamically in round-robin (balanced distribution)
        teams = [{"teamName": f"Team {i + 1}", "members": []} for i in range(number_of_teams)]
        for idx, member in enumerate(pool):
            teams[idx % number_of_teams]["members"].append(member)

        members = [m for t in teams for m in t["members"]]

        avg_exp = round(float(np.mean([float(m.get("experience") or 0) for m in members])), 2)
        avg_skill = round(float(np.mean([float(m.get("skillLevel") or 1) for m in members])), 2)
        avg_perf = round(float(np.mean([float(m.get("performanceRating") or 0) for m in members])), 2)
        avg_match = round(float(np.mean([float(m.get("matchScore") or 0) for m in members])), 2)

        return {
            "teamName": criteria.get("teamName"),
            "projectName": criteria.get("projectName"),
            "projectPriority": criteria.get("projectPriority", "Medium"),
            "algorithm": "python-kmeans-attention",
            "numberOfTeams": number_of_teams,
            "kmeans": {
                "selectedK": int(best_k),
                "minK": int(config.get("minClusters", 2)),
                "maxK": int(config.get("maxClusters", 8)),
                "selectedCluster": int(best_cluster),
            },
            "statistics": {
                "avgExperience": avg_exp,
                "avgSkillLevel": avg_skill,
                "avgPerformance": avg_perf,
                "avgMatchScore": avg_match,
                "totalMembers": len(members),
            },
            "teams": teams,
            "members": members,
        }
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Team generation failed in Python API: {str(ex)}",
        ) from ex


@APP.post("/api/team/generate")
def generate_team(payload: TeamGenerateRequest):
    return _generate_team(payload.model_dump())


@APP.post("/api/ml/team-formation")
def ml_team_formation(payload: TeamGenerateRequest):
    """
    Alias endpoint for Spring Boot backend.
    Use this endpoint when your Java service calls the Python ML model.
    """
    return _generate_team(payload.model_dump())


@APP.get("/api/team/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("team_api:APP", host="0.0.0.0", port=5000, reload=True)
