"""
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    AI-POWERED SKILL-BASED TEAM FORMATION SYSTEM
    
    A production-grade machine learning system for intelligent team formation
    using K-Means clustering with attention-based feature weighting.
    
    Features:
    â€¢ Automated feature engineering from raw employee data
    â€¢ Dynamic attention mechanism for feature importance
    â€¢ Optimal cluster selection using Silhouette analysis
    â€¢ Comprehensive team statistics and insights
    â€¢ Production-ready error handling and logging
    
    Author: HRM System | Version: 1.0 | Date: 2026
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
"""

import pandas as pd
import numpy as np
import os
import sys
import warnings
from datetime import datetime
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

CONFIG = {
    'CURRENT_YEAR': 2026,
    'MIN_CLUSTERS': 2,
    'MAX_CLUSTERS': 8,
    'KMEANS_INIT': 'k-means++',
    'KMEANS_N_INIT': 20,
    'RANDOM_STATE': 42,
    'MULTI_SEED_SEARCH': [11, 23, 42, 67, 89],
    'ATTENTION_PROBE_K': 4,
    'OUTPUT_WIDTH': 85,
    'BASE_FEATURES': [
        'Skill Level',
        'Experience',
        'Performance Rating',
        'Availability Score',
        'Category Encoded',
        'Department Encoded',
        'Role Encoded',
        'Skill Count'
    ],
    'SKILLS': [
        'frontend', 'backend', 'data_science', 'database_design',
        'devops', 'security', 'leadership', 'ux_design', 
        'testing', 'analytics', 'project_management', 'communication'
    ],
    # Skill aliases to avoid missed requirements due to naming mismatches
    'SKILL_ALIASES': {
        'databases': 'database_design',
        'database': 'database_design',
        'ui_ux': 'ux_design',
        'pm': 'project_management'
    },
    'AVAILABILITY_MAP': {
        'available': 1.0,
        'busy': 0.6,
        'on leave': 0.2,
        'unavailable': 0.0
    }
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_header(text, char='='):
    """Print formatted section header."""
    width = CONFIG['OUTPUT_WIDTH']
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}\n")


def print_section(text):
    """Print formatted section subheader."""
    print(f"\n{'-' * CONFIG['OUTPUT_WIDTH']}")
    print(f"  {text}")
    print(f"{'-' * CONFIG['OUTPUT_WIDTH']}\n")


def log_step(step_num, title, details=""):
    """Log completed step."""
    status = "[OK]"
    message = f"{status} STEP {step_num}: {title}"
    if details:
        message += f" | {details}"
    print(message)


def build_feature_list(df):
    """Build full feature list from base features and skill indicators."""
    skill_cols = [f"skill_{s}" for s in CONFIG['SKILLS']]
    features = CONFIG['BASE_FEATURES'] + skill_cols
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")
    return features


# ============================================================================
# STEP 1: DATA LOADING
# ============================================================================

def load_employee_data():
    """
    Load employee data from CSV file.
    
    Returns:
        pd.DataFrame: Raw employee data
        str: Path to the loaded file
    
    Raises:
        FileNotFoundError: If CSV file not found
    """
    print_header("STEP 1: DATA LOADING & VALIDATION")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'employees.csv')
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"[ERROR] File not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    log_step(1, "Data Loaded", f"{len(df)} employees | {len(df.columns)} columns")
    print(f"  File: {csv_path}")
    print(f"  Size: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    print(f"  Columns: {', '.join(df.columns.tolist())}")
    
    return df, csv_path


# ============================================================================
# STEP 2: DATA PREPROCESSING & CLEANING
# ============================================================================

def preprocess_data(df):
    """
    Clean and preprocess employee data.
    
    Performs:
    â€¢ Missing value handling (forward fill)
    â€¢ Column normalization to HR schema
    â€¢ Categorical encoding (Category, Department, Role)
    â€¢ Availability normalization to numeric score
    
    Args:
        pd.DataFrame: Raw employee data
    
    Returns:
        pd.DataFrame: Preprocessed data
        dict: Encoders used for categorical variables
    """
    print_section("STEP 2: DATA PREPROCESSING")
    
    df_clean = df.copy()
    
    # Count missing values before
    missing_before = df_clean.isnull().sum().sum()
    
    # Handle missing values
    df_clean = df_clean.fillna(method='ffill')
    
    missing_after = df_clean.isnull().sum().sum()
    log_step(2, "Missing Values Processed", 
             f"Before: {missing_before} | After: {missing_after}")
    
    # Normalize column names to expected HR schema
    column_map = {
        'employee id': 'Employee ID',
        'employee_id': 'Employee ID',
        'id': 'Employee ID',
        'name': 'Name',
        'skills': 'Skills',
        'skill level': 'Skill Level',
        'skilllevel': 'Skill Level',
        'experience': 'Experience',
        'experience (years)': 'Experience',
        'category': 'Category',
        'availability': 'Availability',
        'performance rating': 'Performance Rating',
        'performance': 'Performance Rating',
        'department': 'Department',
        'role': 'Role'
    }
    normalized_cols = {}
    for col in df_clean.columns:
        key = str(col).strip().lower()
        normalized_cols[col] = column_map.get(key, col)
    df_clean = df_clean.rename(columns=normalized_cols)

    required_cols = [
        'Name',
        'Skills',
        'Skill Level',
        'Experience',
        'Category',
        'Availability',
        'Performance Rating',
        'Department',
        'Role'
    ]
    missing_cols = [c for c in required_cols if c not in df_clean.columns]
    if missing_cols:
        raise ValueError(f"Missing required CSV columns: {missing_cols}")

    # Availability to numeric score
    df_clean['Availability'] = df_clean.get('Availability', '').astype(str).str.strip()
    df_clean['Availability Score'] = (
        df_clean['Availability'].str.lower().map(CONFIG['AVAILABILITY_MAP']).fillna(0.5)
    )

    # Numeric conversions
    df_clean['Skill Level'] = pd.to_numeric(df_clean.get('Skill Level', 0), errors='coerce').fillna(0)
    df_clean['Experience'] = pd.to_numeric(df_clean.get('Experience', 0), errors='coerce').fillna(0)
    df_clean['Performance Rating'] = pd.to_numeric(df_clean.get('Performance Rating', 0), errors='coerce').fillna(0)

    # Encode categorical fields
    category_encoder = LabelEncoder()
    dept_encoder = LabelEncoder()
    role_encoder = LabelEncoder()

    df_clean['Category'] = df_clean.get('Category', 'Unknown').astype(str).fillna('Unknown')
    df_clean['Department'] = df_clean.get('Department', 'Unknown').astype(str).fillna('Unknown')
    df_clean['Role'] = df_clean.get('Role', 'Unknown').astype(str).fillna('Unknown')

    df_clean['Category Encoded'] = category_encoder.fit_transform(df_clean['Category'])
    df_clean['Department Encoded'] = dept_encoder.fit_transform(df_clean['Department'])
    df_clean['Role Encoded'] = role_encoder.fit_transform(df_clean['Role'])

    print("  * Categorical Encoded: Category, Department, Role")

    encoders = {
        'category': category_encoder,
        'department': dept_encoder,
        'role': role_encoder
    }
    
    return df_clean, encoders


# ============================================================================
# STEP 3: FEATURE ENGINEERING
# ============================================================================

def engineer_features(df):
    """
    Create derived features from raw data.
    
    Creates:
    â€¢ Skill indicators from multi-skill text
    â€¢ Skill count
    
    Args:
        pd.DataFrame: Preprocessed data
    
    Returns:
        pd.DataFrame: Data with new features
    """
    print_section("STEP 3: FEATURE ENGINEERING")
    
    df_features = df.copy()

    def extract_skill_tokens(text):
        return [t.strip().lower() for t in str(text).split(',') if t.strip()]

    skill_keywords = {
        'frontend': ['react', 'angular', 'vue', 'html', 'css', 'javascript', 'frontend'],
        'backend': ['node', 'java', 'spring', 'django', 'backend', 'api'],
        'data_science': ['ml', 'machine learning', 'data science', 'python', 'model', 'data'],
        'database_design': ['sql', 'database', 'db', 'mysql', 'postgres', 'mongodb'],
        'devops': ['devops', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'ci/cd'],
        'security': ['security', 'infosec', 'compliance'],
        'leadership': ['lead', 'manager', 'senior', 'director', 'head'],
        'ux_design': ['ux', 'ui', 'design', 'figma'],
        'testing': ['testing', 'qa', 'automation', 'selenium'],
        'analytics': ['analytics', 'bi', 'dashboard', 'report', 'data'],
        'project_management': ['project', 'pm', 'scrum', 'agile'],
        'communication': ['communication', 'presentation', 'stakeholder']
    }

    skill_indicator = {skill: [] for skill in CONFIG['SKILLS']}
    skill_counts = []

    for _, row in df_features.iterrows():
        tokens = set(extract_skill_tokens(row.get('Skills', '')))
        tokens.update(extract_skill_tokens(row.get('Role', '')))
        tokens.update(extract_skill_tokens(row.get('Department', '')))

        active_skills = set()
        for skill, keywords in skill_keywords.items():
            for kw in keywords:
                if any(kw in token for token in tokens):
                    active_skills.add(skill)
                    break

        for skill in CONFIG['SKILLS']:
            skill_indicator[skill].append(1 if skill in active_skills else 0)

        skill_counts.append(len(active_skills))

    for skill in CONFIG['SKILLS']:
        df_features[f'skill_{skill}'] = skill_indicator[skill]
    df_features['Skill Count'] = skill_counts

    log_step(3, "Feature Engineering Complete", "Skill indicators and counts created")
    
    return df_features


# ============================================================================
# STEP 4: FEATURE SELECTION & NORMALIZATION
# ============================================================================

def select_and_scale_features(df, features_list):
    """
    Select clustering features and normalize to unit scale.
    
    Args:
        pd.DataFrame: Processed employee data
        list: Feature names to use
    
    Returns:
        np.ndarray: Normalized feature matrix
        StandardScaler: Fitted scaler object
    """
    print_section("STEP 4: FEATURE SELECTION & SCALING")
    
    print(f"  Selected Features ({len(features_list)}):")
    for i, feat in enumerate(features_list, 1):
        print(f"    {i}. {feat}")
    
    X = df[features_list].copy()
    
    # Display statistics before scaling
    print(f"\n  Statistics Before Scaling:")
    stats_df = pd.DataFrame({
        'Feature': features_list,
        'Min': X.min().values,
        'Mean': X.mean().values,
        'Max': X.max().values,
        'Std': X.std().values
    })
    print(stats_df.to_string(index=False))
    
    # Apply StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    log_step(4, "Feature Scaling Complete", 
             f"Shape: {X_scaled.shape} | Method: StandardScaler (Z-score)")
    
    return X_scaled, scaler


# ============================================================================
# STEP 5: ATTENTION MECHANISM (Dynamic Feature Weighting)
# ============================================================================

def compute_attention_weights(X_scaled, features_list):
    """
    Compute dynamic attention weights using feature separability.
    
    Uses:
    â€¢ Variance to measure feature spread/importance
    â€¢ Standard deviation for additional perspective
    â€¢ Softmax normalization for probability distribution
    
    Args:
        np.ndarray: Scaled feature matrix
        list: Feature names
    
    Returns:
        np.ndarray: Attention weights (normalized)
        dict: Additional statistics
    """
    print_section("STEP 5: ATTENTION MECHANISM (Feature Importance)")
    
    print("  Discriminative Analysis:")
    print("    * Building provisional clusters to estimate feature separation power")

    n_samples = X_scaled.shape[0]
    if n_samples < 2:
        raise ValueError("Attention weighting requires at least 2 samples.")
    probe_k = min(max(2, CONFIG['ATTENTION_PROBE_K']), max(2, n_samples - 1))

    probe_model = KMeans(
        n_clusters=probe_k,
        init=CONFIG['KMEANS_INIT'],
        n_init=CONFIG['KMEANS_N_INIT'],
        random_state=CONFIG['RANDOM_STATE']
    )
    probe_labels = probe_model.fit_predict(X_scaled)

    feature_variance = np.var(X_scaled, axis=0)
    feature_std = np.std(X_scaled, axis=0)
    fisher_scores = []

    for feat_idx in range(X_scaled.shape[1]):
        feature_values = X_scaled[:, feat_idx]
        global_mean = np.mean(feature_values)

        between_var = 0.0
        within_var = 0.0

        for cluster_id in np.unique(probe_labels):
            cluster_values = feature_values[probe_labels == cluster_id]
            if len(cluster_values) == 0:
                continue
            cluster_mean = np.mean(cluster_values)
            between_var += len(cluster_values) * (cluster_mean - global_mean) ** 2
            within_var += np.sum((cluster_values - cluster_mean) ** 2)

        fisher_score = between_var / (within_var + 1e-9)
        fisher_scores.append(float(fisher_score))

    fisher_scores = np.array(fisher_scores)

    # Softmax on normalized Fisher scores gives stable, non-uniform feature attention
    fisher_norm = (fisher_scores - np.mean(fisher_scores)) / (np.std(fisher_scores) + 1e-9)
    exp_scores = np.exp(fisher_norm)
    attention_weights = exp_scores / np.sum(exp_scores)

    weight_stats = {
        'variance': feature_variance,
        'std_dev': feature_std,
        'fisher_scores': fisher_scores,
        'weights': attention_weights,
        'probe_k': probe_k
    }

    log_step(5, "Attention Weights Computed",
             f"Using Fisher separability scores with Softmax normalization")

    print(f"\n  {'Feature':<30} {'Fisher Score':<15} {'Weight':<12} {'Impact'}")
    print(f"  {'-' * 80}")
    for feat, score, weight in zip(features_list, fisher_scores, attention_weights):
        impact = '*' * int(weight * 50)
        print(f"  {feat:<30} {score:>13.6f}   {weight:>10.4f}   {impact}")
    
    return attention_weights, weight_stats


# ============================================================================
# PHASE 1: ATTENTION-BASED SKILL WEIGHTING
# ============================================================================

def define_employee_skills(df):
    """
    Define numeric skill vectors for employees based on their profile.
    
    Generates skill vectors based on:
    - Parsed skills from CSV
    - Skill level weighting
    
    Args:
        pd.DataFrame: Employee data
    
    Returns:
        np.ndarray: Skill matrix (employees x skills)
    """
    print_section("SKILL PROFILING: CONVERT PROFILES TO VECTORS")
    
    num_employees = len(df)
    num_skills = len(CONFIG['SKILLS'])
    skill_matrix = np.zeros((num_employees, num_skills))
    
    level = df['Skill Level'].values.astype(float)
    level_norm = level / max(1.0, level.max())

    for i, skill in enumerate(CONFIG['SKILLS']):
        indicator = df[f'skill_{skill}'].values.astype(float)
        skill_matrix[:, i] = indicator * level_norm
    
    # Normalize to [0, 1]
    skill_matrix = np.clip(skill_matrix, 0, 1)
    
    print(f"  Skill Matrix Shape: {skill_matrix.shape} (employees x skills)")
    print(f"  Skills Defined: {len(CONFIG['SKILLS'])}")
    print(f"  Skills: {', '.join(CONFIG['SKILLS'][:6])}")
    print(f"  Mean Skill Probability: {skill_matrix.mean():.4f}\n")
    
    return skill_matrix


def compute_skill_similarity(employee_skills, project_requirements):
    """
    Compute cosine similarity between employee skills and project requirements.
    
    Uses dot product of normalized vectors to measure alignment.
    
    Args:
        np.ndarray: Employee skill vector
        np.ndarray: Project requirement vector
    
    Returns:
        float: Similarity score (0-1, higher = better match)
    """
    # Normalize vectors
    emp_norm = np.linalg.norm(employee_skills)
    proj_norm = np.linalg.norm(project_requirements)
    
    if emp_norm == 0 or proj_norm == 0:
        return 0.0
    
    emp_normalized = employee_skills / emp_norm
    proj_normalized = project_requirements / proj_norm
    
    # Cosine similarity = dot product of normalized vectors
    similarity = np.dot(emp_normalized, proj_normalized)
    
    return float(np.clip(similarity, 0, 1))


def apply_attention_to_skills(skill_matrix, project_requirement_vector):
    """
    Apply attention mechanism to weight employee skills by project relevance.
    
    Generates attention weights based on importance of each skill for project.
    
    Args:
        np.ndarray: Skill matrix (employees x skills)
        np.ndarray: Project priority skills vector
    
    Returns:
        np.ndarray: Attention weights (employees,)
        np.ndarray: Weighted skill vectors
    """
    # Compute similarity for each employee
    similarities = np.array([
        compute_skill_similarity(skill_matrix[i], project_requirement_vector)
        for i in range(skill_matrix.shape[0])
    ])
    
    # Apply softmax for attention weights
    exp_similarities = np.exp(
        3 * (similarities - similarities.mean()) / (similarities.std() + 1e-9)
    )
    attention_weights = exp_similarities / np.sum(exp_similarities)
    
    # Weight skill vectors by attention
    weighted_skills = skill_matrix * attention_weights.reshape(-1, 1)
    
    return attention_weights, weighted_skills, similarities


def rank_employees_by_similarity(df, skill_matrix, project_req, project_name):
    """
    Rank employees by similarity to project requirements.
    
    Combines skill similarity with traditional criteria.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Skill matrix
        ProjectRequirement: Project requirements
        str: Project name for display
    
    Returns:
        pd.DataFrame: Ranking with scores
    """
    # Create project skill vector
    project_vector = np.zeros(len(CONFIG['SKILLS']))
    total_weight = sum(project_req.priority_skills.values())
    
    for skill, weight in project_req.priority_skills.items():
        if skill in CONFIG['SKILLS']:
            idx = CONFIG['SKILLS'].index(skill)
            project_vector[idx] = weight / total_weight
    
    # Compute attention and similarities
    attention_weights, weighted_skills, similarities = apply_attention_to_skills(
        skill_matrix, project_vector
    )
    
    # Create ranking dataframe
    ranking = pd.DataFrame({
        'Name': df['Name'].values,
        'Experience': df['Experience'].values,
        'Skill Level': df['Skill Level'].values,
        'Performance Rating': df['Performance Rating'].values,
        'Skill_Similarity': similarities,
        'Attention_Weight': attention_weights
    })
    
    # Overall score: balance skill similarity and experience
    ranking['Overall_Score'] = (
        0.5 * ranking['Skill_Similarity'] +
        0.3 * (ranking['Experience'] / ranking['Experience'].max()) +
        0.2 * (ranking['Performance Rating'] / ranking['Performance Rating'].max())
    )
    
    ranking = ranking.sort_values('Overall_Score', ascending=False).reset_index(drop=True)
    ranking['Rank'] = range(1, len(ranking) + 1)
    
    return ranking


# ============================================================================


def find_optimal_clusters(X_weighted, min_k=2, max_k=8):
    """
    Find optimal number of clusters using robust multi-metric selection.
    
    Evaluates:
    â€¢ Silhouette Score (cluster cohesion and separation)
    â€¢ Calinski-Harabasz Index (variance ratio)
    
    Args:
        np.ndarray: Feature matrix with attention weights applied
        int: Minimum clusters to test
        int: Maximum clusters to test
    
    Returns:
        int: Optimal number of clusters
        list: Evaluation results for all K values
    """
    print_section("STEP 6: OPTIMAL CLUSTER SELECTION")
    
    print(f"  Evaluating K from {min_k} to {max_k}...")
    print(f"  Metrics: Silhouette | Calinski-Harabasz | Davies-Bouldin | Composite Score\n")
    
    evaluation_results = []
    
    for k in range(min_k, max_k + 1):
        best_seed_run = None

        # Multi-seed search improves robustness for each K
        for seed in CONFIG['MULTI_SEED_SEARCH']:
            kmeans = KMeans(
                n_clusters=k,
                init=CONFIG['KMEANS_INIT'],
                n_init=CONFIG['KMEANS_N_INIT'],
                random_state=seed
            )
            cluster_labels = kmeans.fit_predict(X_weighted)

            if len(np.unique(cluster_labels)) < 2:
                continue

            silhouette_avg = silhouette_score(X_weighted, cluster_labels)
            calinski_index = calinski_harabasz_score(X_weighted, cluster_labels)
            davies_index = davies_bouldin_score(X_weighted, cluster_labels)

            current_result = {
                'k': k,
                'seed': seed,
                'silhouette': silhouette_avg,
                'calinski': calinski_index,
                'davies_bouldin': davies_index,
                'inertia': kmeans.inertia_
            }

            if best_seed_run is None or current_result['silhouette'] > best_seed_run['silhouette']:
                best_seed_run = current_result

        if best_seed_run is None:
            continue
        
        evaluation_results.append(best_seed_run)
        
        # Print results
        sil_bar = '*' * int(best_seed_run['silhouette'] * 40)
        print(
            f"  K = {k} | Silhouette: {best_seed_run['silhouette']:>7.4f} {sil_bar:<40} "
            f"| C-H: {best_seed_run['calinski']:>10.2f} | D-B: {best_seed_run['davies_bouldin']:.4f}"
        )

    if not evaluation_results:
        raise ValueError("Unable to evaluate clustering quality for the provided data.")

    # Composite scoring across metrics
    sil_values = np.array([r['silhouette'] for r in evaluation_results])
    ch_values = np.array([r['calinski'] for r in evaluation_results])
    db_values = np.array([r['davies_bouldin'] for r in evaluation_results])

    sil_norm = (sil_values - sil_values.min()) / (sil_values.max() - sil_values.min() + 1e-9)
    ch_norm = (ch_values - ch_values.min()) / (ch_values.max() - ch_values.min() + 1e-9)
    db_inv_norm = (db_values.max() - db_values) / (db_values.max() - db_values.min() + 1e-9)

    for i, result in enumerate(evaluation_results):
        result['composite'] = float(0.50 * sil_norm[i] + 0.30 * ch_norm[i] + 0.20 * db_inv_norm[i])

    best_result = max(evaluation_results, key=lambda x: x['composite'])
    best_k = best_result['k']
    best_score = best_result['composite']
    
    print(f"\n  {'-' * 70}")
    print(
        f"  [BEST] Optimal K Selected: {best_k} "
        f"(Composite: {best_score:.4f} | Silhouette: {best_result['silhouette']:.4f} | "
        f"C-H: {best_result['calinski']:.2f} | D-B: {best_result['davies_bouldin']:.4f})"
    )
    print(f"  {'-' * 70}")
    
    log_step(6, "Optimal Cluster Count Determined", 
             f"K={best_k} with Composite Score={best_score:.4f}")
    
    return best_k, evaluation_results


# ============================================================================
# STEP 7: FINAL CLUSTERING & TEAM ASSIGNMENT
# ============================================================================

def perform_final_clustering(X_weighted, optimal_k):
    """
    Perform final K-Means clustering with optimal K.
    
    Args:
        np.ndarray: Feature matrix with attention weights
        int: Optimal number of clusters
    
    Returns:
        np.ndarray: Cluster labels for each sample
        KMeans: Fitted KMeans model
    """
    print_section("STEP 7: FINAL CLUSTERING")
    
    print(f"  Performing K-Means with K={optimal_k}...")
    print(f"  Configuration:")
    print(f"    * Initialization: {CONFIG['KMEANS_INIT']}")
    print(f"    * N Initializations: {CONFIG['KMEANS_N_INIT']}")
    print(f"    * Random State Candidates: {CONFIG['MULTI_SEED_SEARCH']}")

    best_model = None
    best_labels = None
    best_silhouette = -1.0
    best_seed = CONFIG['RANDOM_STATE']

    for seed in CONFIG['MULTI_SEED_SEARCH']:
        candidate = KMeans(
            n_clusters=optimal_k,
            init=CONFIG['KMEANS_INIT'],
            n_init=CONFIG['KMEANS_N_INIT'],
            random_state=seed
        )
        candidate_labels = candidate.fit_predict(X_weighted)
        if len(np.unique(candidate_labels)) < 2:
            continue
        current_silhouette = silhouette_score(X_weighted, candidate_labels)
        if current_silhouette > best_silhouette:
            best_silhouette = current_silhouette
            best_model = candidate
            best_labels = candidate_labels
            best_seed = seed

    if best_model is None or best_labels is None:
        raise ValueError("Final clustering failed to produce valid clusters.")
    
    log_step(7, "Final Clustering Complete", 
             f"Inertia: {best_model.inertia_:.2f} | Silhouette: {best_silhouette:.4f} | Seed: {best_seed}")
    
    return best_labels, best_model


# ============================================================================
# STEP 8: TEAM ANALYSIS & RESULTS
# ============================================================================

def analyze_and_display_teams(df, cluster_labels):
    """
    Analyze team composition and display comprehensive results.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Cluster assignments
    """
    print_header("STEP 8: TEAM ANALYSIS & RESULTS")
    
    df_teams = df.copy()
    df_teams['Team_ID'] = cluster_labels
    
    print(f"\nTeam Distribution:")
    print(f"  Total Teams: {df_teams['Team_ID'].nunique()}")
    print(f"  Total Employees: {len(df_teams)}\n")
    
    # Analyze each team
    for team_id in sorted(df_teams['Team_ID'].unique()):
        team_data = df_teams[df_teams['Team_ID'] == team_id]
        
        print(f"{'=' * CONFIG['OUTPUT_WIDTH']}")
        print(f"  TEAM {team_id} | Size: {len(team_data)} members")
        print(f"{'=' * CONFIG['OUTPUT_WIDTH']}\n")
        
        # Display team members
        team_display = team_data[['Name', 'Department', 'Role', 'Experience', 'Skill Level', 'Performance Rating']].copy()
        team_display_sorted = team_display.sort_values('Performance Rating', ascending=False)
        print(team_display_sorted.to_string(index=False))
        
        # Team statistics
        print(f"\n  Team Statistics:")
        print(f"    * Avg Experience: {team_data['Experience'].mean():.1f} years")
        print(f"    * Avg Skill Level: {team_data['Skill Level'].mean():.2f}")
        print(f"    * Avg Performance: {team_data['Performance Rating'].mean():.2f}")
        print(f"    * Avg Availability Score: {team_data['Availability Score'].mean():.2f}")
        print()


# ============================================================================
# PARAMETER DISPLAY FUNCTIONS - Show basis and reasoning for team formation
# ============================================================================

def display_feature_scaling_basis(scaler, features_list):
    """
    Show the mathematical basis for feature scaling.
    
    Args:
        StandardScaler: Fitted scaler
    """
    print_section("FEATURE SCALING: WHY NORMALIZATION?")
    
    print("[STANDARDIZATION] Z-Score Normalization\n")
    print("Problem: Features have different scales")
    print("  * Skill Level: 1 - 10 (small numbers)")
    print("  * Experience: 0 - 20 (years)")
    print("  * Performance Rating: 0 - 10 (scores)")
    print("  * Availability Score: 0.0 - 1.0 (normalized)\n")
    
    print("Solution: Convert all features to same scale (mean=0, std=1)")
    print("Formula: Z = (X - Mean) / Standard Deviation\n")
    
    print(f"{'Feature':<30} {'Mean':<18} {'Std Dev':<18}")
    print(f"{'-' * 66}")
    for i, feat in enumerate(features_list):
        print(f"{feat:<30} {scaler.mean_[i]:>16.4f}  {scaler.scale_[i]:>16.4f}")
    
    print(f"\n[RESULT] All features now on equal footing for clustering")


def display_clustering_parameters(df_features, attention_weights, weight_stats, features_list):
    """
    Display detailed clustering parameters and decision basis.
    
    Shows users what features matter most and why.
    
    Args:
        pd.DataFrame: Employee data with features
        np.ndarray: Attention weights
        dict: Weight statistics
    """
    print_section("CLUSTERING PARAMETERS & DECISION BASIS")
    
    print("[FEATURE IMPORTANCE] Feature Contribution To Team Formation\n")
    
    # Feature reasoning map
    reasoning_map = {
        'Skill Level': 'Weights depth of expertise',
        'Experience': 'Balances junior and senior talent',
        'Performance Rating': 'Rewards strong performance',
        'Availability Score': 'Aligns team availability',
        'Category Encoded': 'Balances employment category',
        'Department Encoded': 'Promotes cross-department coverage',
        'Role Encoded': 'Distributes role diversity',
        'Skill Count': 'Encourages multi-skill coverage'
    }
    
    print(f"{'Feature':<25} {'Weight':<12} {'Impact %':<12} {'Reasoning'}")
    print(f"{'-' * 85}")
    
    for feat, weight in zip(features_list, attention_weights):
        impact_pct = weight * 100
        bar = '*' * int(weight * 30)
        reasoning = reasoning_map.get(feat, 'Feature importance measure')
        print(f"{feat:<25} {weight:>10.4f}   {impact_pct:>10.2f}%  {bar:<15} {reasoning}")
    
    # Discriminative analysis
    print(f"\n\n[DISCRIMINATIVE ANALYSIS] Feature Separation Power\n")
    print(f"{'Feature':<25} {'Fisher Score':<15} {'Std Dev':<15} {'Interpretation'}")
    print(f"{'-' * 85}")
    
    interpretation_map = {
        'Skill Level': 'Higher separation = expertise differentiates teams',
        'Experience': 'Separation reflects seniority differences',
        'Performance Rating': 'Performance differentiates teams',
        'Availability Score': 'Availability patterns separate teams',
        'Category Encoded': 'Category impacts clustering',
        'Department Encoded': 'Department diversity impacts clustering',
        'Role Encoded': 'Role specialization separates teams',
        'Skill Count': 'Multi-skill coverage separates teams'
    }
    
    for feat, score, std in zip(features_list, weight_stats['fisher_scores'], weight_stats['std_dev']):
        interp = interpretation_map.get(feat, 'Statistical measure')
        print(f"{feat:<25} {score:>13.6f}  {std:>13.6f}  {interp}")
    
    # Data statistics
    print(f"\n\n[EMPLOYEE DATA STATISTICS] Basis for Clustering\n")
    
    stats_data = {
        'Skill Level': {
            'min': df_features['Skill Level'].min(),
            'max': df_features['Skill Level'].max(),
            'mean': df_features['Skill Level'].mean(),
            'unit': 'level'
        },
        'Experience': {
            'min': df_features['Experience'].min(),
            'max': df_features['Experience'].max(),
            'mean': df_features['Experience'].mean(),
            'unit': 'years'
        },
        'Performance Rating': {
            'min': df_features['Performance Rating'].min(),
            'max': df_features['Performance Rating'].max(),
            'mean': df_features['Performance Rating'].mean(),
            'unit': 'score'
        },
        'Availability Score': {
            'min': df_features['Availability Score'].min(),
            'max': df_features['Availability Score'].max(),
            'mean': df_features['Availability Score'].mean(),
            'unit': 'score'
        }
    }
    
    print(f"{'Metric':<25} {'Min':<15} {'Max':<15} {'Mean':<15} {'Unit'}")
    print(f"{'-' * 75}")
    
    for metric, stats in stats_data.items():
        print(f"{metric:<25} {stats['min']:>13.2f}  {stats['max']:>13.2f}  {stats['mean']:>13.2f}  {stats['unit']}")
    
    # Category distribution
    print(f"\n\n[CATEGORY DISTRIBUTION] In Dataset\n")
    category_counts = df_features['Category'].value_counts()
    total = len(df_features)
    for cat, count in category_counts.items():
        print(f"{cat:<25} {count:>6} employees ({count/total*100:>5.1f}%)")


def display_team_formation_logic(optimal_k, eval_results):
    """
    Explain WHY specific number of clusters was chosen.
    
    Args:
        int: Optimal K value
        list: Evaluation results
    """
    print_section("TEAM FORMATION LOGIC & DECISION MAKING")
    
    print("[DECISION] WHY THESE TEAMS?\n")
    
    best_result = max(eval_results, key=lambda x: x.get('composite', x['silhouette']))
    
    print(f"The system evaluated team sizes from {eval_results[0]['k']} to {eval_results[-1]['k']} members.\n")
    print(f"Decision Metrics Used:")
    print(f"  1. Silhouette Score - Measures how well employees fit within their team")
    print(f"     (Range: -1 to +1, higher is better)")
    print(f"  2. Calinski-Harabasz Index - Measures team separation quality")
    print(f"     (Higher values indicate better defined clusters)")
    print(f"  3. Davies-Bouldin Index - Measures overlap between teams")
    print(f"     (Lower values are better)")
    print(f"  4. Composite Score = weighted blend of all above metrics\n")
    
    print(f"Evaluation Results:")
    print(f"{'K':<6} {'Silhouette':<12} {'Calinski-H':<14} {'Davies-B':<12} {'Composite':<12} {'Quality':<14}")
    print(f"{'-' * 86}")
    
    for result in eval_results:
        k = result['k']
        sil = result['silhouette']
        cal = result['calinski']
        db = result.get('davies_bouldin', 0.0)
        comp = result.get('composite', sil)
        
        # Quality indicator
        if sil >= 0.3:
            quality = "[EXCELLENT]"
        elif sil >= 0.2:
            quality = "[GOOD]"
        elif sil >= 0.1:
            quality = "[FAIR]"
        else:
            quality = "[POOR]"
        
        marker = "  (SELECTED)" if k == best_result['k'] else ""
        print(f"{k:<6} {sil:<12.4f} {cal:<14.2f} {db:<12.4f} {comp:<12.4f} {quality:<14}{marker}")
    
    print(f"\n[RESULT SUMMARY]")
    print(f"   {optimal_k} teams were formed because they achieved the best balance")
    print(f"   between cohesion (employees similar within team) and separation")
    print(f"   (teams distinct from each other).")
    print(f"\n   Composite Score: {best_result.get('composite', best_result['silhouette']):.4f}")
    print(f"   Silhouette Score: {best_result['silhouette']:.4f}")
    quality_text = 'EXCELLENT' if best_result['silhouette'] >= 0.3 else 'GOOD' if best_result['silhouette'] >= 0.2 else 'ACCEPTABLE'
    print(f"   This indicates {quality_text} team quality.")


# ============================================================================
# PROJECT ASSIGNMENT & TEAM MATCHING
# ============================================================================

class ProjectRequirement:
    """Define project requirements for team formation."""
    
    def __init__(self, project_id, name, required_team_size, min_experience,
                 max_budget, priority_skills, deadline_days=30):
        """
        Initialize project requirements.
        
        Args:
            project_id: Unique project identifier
            name: Project name
            required_team_size: Number of employees needed
            min_experience: Minimum years of experience required
            max_budget: Maximum salary budget for project
            priority_skills: Dict of skills {skill_name: importance_weight}
            deadline_days: Days to complete project
        """
        self.project_id = project_id
        self.name = name
        self.required_team_size = required_team_size
        self.min_experience = min_experience
        self.max_budget = max_budget
        # Normalize and validate required skills to prevent silent misses
        normalized = {}
        for skill, weight in priority_skills.items():
            canonical = CONFIG['SKILL_ALIASES'].get(skill, skill)
            normalized[canonical] = weight
        missing = [s for s in normalized.keys() if s not in CONFIG['SKILLS']]
        if missing:
            raise ValueError(
                f"Unknown skill(s) in project requirements: {missing}. "
                f"Valid skills: {CONFIG['SKILLS']}"
            )
        self.priority_skills = normalized
        self.deadline_days = deadline_days
        self.assigned_team = []
        self.total_salary = 0
        self.avg_experience = 0
        self.match_score = 0.0


def score_employee_for_project(employee, project_req):
    """
    Calculate how well an employee matches project requirements.
    
    Args:
        employee: Employee data (pandas Series)
        project_req: ProjectRequirement object
    
    Returns:
        float: Match score (0-100)
    """
    score = 0.0

    # Experience requirement (0-30)
    if employee['Experience'] >= project_req.min_experience:
        score += 30
    else:
        exp_ratio = employee['Experience'] / max(1, project_req.min_experience)
        score += 30 * exp_ratio

    # Performance rating (0-25), assume 0-10 scale
    score += min(25, (employee['Performance Rating'] / 10) * 25)

    # Availability score (0-15)
    score += min(15, employee['Availability Score'] * 15)

    # Skill level (0-15), assume 1-10 scale
    score += min(15, (employee['Skill Level'] / 10) * 15)

    # Skill match to project priorities (0-15)
    required_skills = [s for s in project_req.priority_skills.keys() if s in CONFIG['SKILLS']]
    if required_skills:
        hits = sum(1 for s in required_skills if employee.get(f'skill_{s}', 0) == 1)
        score += (hits / len(required_skills)) * 15

    return min(100.0, score)


def assign_teams_to_project(df_features, cluster_labels, projects_list):
    """
    Form and assign teams from clusters to projects based on requirements.
    
    Args:
        pd.DataFrame: Employee data with features
        np.ndarray: Cluster assignments
        list: List of ProjectRequirement objects
    
    Returns:
        list: Updated projects with assigned teams
    """
    df_temp = df_features.copy()
    df_temp['Cluster'] = cluster_labels
    df_temp['Project'] = None
    df_temp['Match_Score'] = 0.0
    
    # Score all employees for all projects
    for project in projects_list:
        df_temp[f'Score_{project.project_id}'] = df_temp.apply(
            lambda row: score_employee_for_project(row, project), axis=1
        )
    
    # Assign employees to projects
    assigned_count = 0
    for project in projects_list:
        # Get unassigned employees
        available = df_temp[df_temp['Project'].isna()].copy()
        
        if len(available) == 0:
            print(f"\n[WARNING] No available employees for project {project.name}")
            continue
        
        # Sort by project-specific score
        available = available.sort_values(f'Score_{project.project_id}', ascending=False)
        
        # Select required team size
        team = available.head(project.required_team_size)
        
        if len(team) < project.required_team_size:
            print(f"[WARNING] Not enough employees for project {project.name}")
            print(f"  Required: {project.required_team_size}, Available: {len(team)}")
        
        # Assign team to project
        team_indices = team.index
        df_temp.loc[team_indices, 'Project'] = project.project_id
        df_temp.loc[team_indices, 'Match_Score'] = team[f'Score_{project.project_id}'].values
        
        # Update project with team data
        project.assigned_team = team[
            ['Name', 'Department', 'Role', 'Experience', 'Skill Level', 'Performance Rating', 'Availability Score']
        ].to_dict('records')
        project.total_salary = 0
        project.avg_experience = team['Experience'].mean()
        project.match_score = team[f'Score_{project.project_id}'].mean()
        
        assigned_count += len(team)
    
    return projects_list, df_temp


def display_project_assignments(projects_list, df_assigned):
    """
    Display project assignments and team details.
    
    Args:
        list: Projects with assigned teams
        pd.DataFrame: Employee data with assignments
    """
    print_header("PROJECT ASSIGNMENT RESULTS")
    
    for project in projects_list:
        if not project.assigned_team:
            print(f"\n[NO TEAM] Project {project.name} - No assignment available")
            continue
        
        print(f"\n{'=' * CONFIG['OUTPUT_WIDTH']}")
        print(f"PROJECT: {project.name}")
        print(f"Project ID: {project.project_id}")
        print(f"{'=' * CONFIG['OUTPUT_WIDTH']}\n")
        
        print(f"ASSIGNMENT REQUIREMENTS:")
        print(f"  * Team Size: {project.required_team_size} members")
        print(f"  * Min Experience: {project.min_experience} years")
        print(f"  * Deadline: {project.deadline_days} days")
        print(f"  * Priority Skills: {', '.join(project.priority_skills.keys())}\n")
        
        print(f"ASSIGNED TEAM MEMBERS:")
        print(f"{'-' * CONFIG['OUTPUT_WIDTH']}\n")
        
        team_df = pd.DataFrame(project.assigned_team)
        print(team_df.to_string(index=False))
        
        print(f"\n\nTEAM STATISTICS:")
        print(f"  * Total Members: {len(project.assigned_team)}")
        print(f"  * Avg Experience: {project.avg_experience:.1f} years")
        print(f"  * Match Score: {project.match_score:.2f}/100")
        print()


def display_project_summary(projects_list):
    """Display summary of all project assignments."""
    print_header("PROJECT ASSIGNMENT SUMMARY")
    
    print("\nPROJECT OVERVIEW:")
    print(f"\n{'Project Name':<30} {'Team Size':<12} {'Match Score':<15}")
    print(f"{'-' * 60}")
    
    total_people_assigned = 0
    
    for project in projects_list:
        if project.assigned_team:
            match = f"{project.match_score:.1f}/100"
            people = len(project.assigned_team)
            total_people_assigned += people
            
            print(f"{project.name:<30} {people:<12} {match:<15}")
    
    print(f"{'-' * 60}")
    print(f"\nAGGREGATE METRICS:")
    print(f"  * Total Projects: {len([p for p in projects_list if p.assigned_team])}")
    print(f"  * Total People Assigned: {total_people_assigned}")
    print(f"  * Average Team Size: {total_people_assigned / max(1, len([p for p in projects_list if p.assigned_team])):.1f} members\n")


# ============================================================================
# HR DASHBOARD - COMPREHENSIVE VIEW
# ============================================================================

def display_team_distribution(df_assigned, cluster_labels):
    """
    Display team distribution and composition.
    
    Args:
        pd.DataFrame: Employee data with assignments
        np.ndarray: Cluster labels
    """
    print_section("TEAM DISTRIBUTION DASHBOARD")
    
    cluster_counts = pd.Series(cluster_labels).value_counts().sort_index()
    
    print("Team Sizes and Composition:\n")
    print(f"{'Team':<8} {'Size':<8} {'Percentage':<15} {'Visual':<30}")
    print(f"{'-' * 65}")
    
    total_employees = len(cluster_labels)
    max_size = cluster_counts.max()
    
    for team_id, count in cluster_counts.items():
        percentage = (count / total_employees) * 100
        bar_length = int((count / max_size) * 20)
        bar = '*' * bar_length
        print(f"Team {team_id:<2} {count:<8} {percentage:>6.1f}%         {bar:<30}")
    
    print(f"\n  Total Teams: {len(cluster_counts)}")
    print(f"  Total Employees: {total_employees}")
    print(f"  Average Team Size: {total_employees / len(cluster_counts):.1f}")


def display_employee_workload(df_assigned, projects_list):
    """
    Display employee workload analysis.
    
    Args:
        pd.DataFrame: Employee data with assignments
        list: Project list
    """
    print_section("EMPLOYEE WORKLOAD ANALYSIS")
    
    # Count projects per employee
    workload = df_assigned[df_assigned['Project'].notna()].groupby('Name').size().reset_index(name='Projects')
    workload = workload.sort_values('Projects', ascending=False)
    
    print("Employees with Multiple Projects:\n")
    
    if len(workload[workload['Projects'] > 1]) > 0:
        multi_project = workload[workload['Projects'] > 1]
        print(f"{'Employee':<20} {'Projects':<12} {'Load':<20}")
        print(f"{'-' * 55}")
        for _, row in multi_project.head(10).iterrows():
            load_bar = '*' * row['Projects']
            print(f"{row['Name']:<20} {row['Projects']:<12} {load_bar:<20}")
    else:
        print("  All employees assigned to single projects")
    
    print(f"\n  Assigned Employees: {len(workload)}")
    print(f"  Average Projects per Employee: {workload['Projects'].mean():.2f}")
    print(f"  Max Workload: {workload['Projects'].max()} projects")


def display_skill_gaps(skill_matrix, projects_list, df):
    """
    Display skill gaps analysis for each project.
    
    Args:
        np.ndarray: Skill matrix
        list: Project list
        pd.DataFrame: Employee data
    """
    print_section("SKILL GAPS ANALYSIS")
    
    for project in projects_list:
        if not project.assigned_team:
            continue
        
        print(f"\nProject: {project.name} (ID: {project.project_id})")
        print(f"{'-' * 65}")
        
        # Get assigned employee indices
        assigned_names = [str(member['Name']) for member in project.assigned_team]
        assigned_indices = df[df['Name'].isin(assigned_names)].index.tolist()
        
        # Analyze required vs available skills
        required_skills = list(project.priority_skills.keys())
        total_weight = sum(project.priority_skills.values())
        
        print(f"\nRequired Skills | Importance | Team Coverage")
        print(f"{'-' * 55}")
        
        for skill in required_skills:
            if skill in CONFIG['SKILLS']:
                skill_idx = CONFIG['SKILLS'].index(skill)
                importance = project.priority_skills[skill] / total_weight
                
                # Check team coverage
                if assigned_indices:
                    coverage = skill_matrix[assigned_indices, skill_idx].mean()
                else:
                    coverage = 0
                
                gap = 1.0 - coverage
                gap_indicator = '*' * int(gap * 10)
                status = "[OK]" if gap < 0.3 else "[MEDIUM]" if gap < 0.6 else "[GAP]"
                
                print(f"{skill:<18} {importance:>6.1%}      {coverage:>6.1%}    {status}")
        
        print()


def display_project_team_mapping(df_assigned, projects_list):
    """
    Display project-to-team mapping visualization.
    
    Args:
        pd.DataFrame: Employee data with assignments
        list: Project list
    """
    print_section("PROJECT-TEAM MAPPING")
    
    print("\nProject Assignments by Team/Cluster:\n")
    
    for project in projects_list:
        if not project.assigned_team:
            continue
        
        team_members = project.assigned_team
        print(f"{project.project_id} | {project.name:<40}")
        print(f"  ['Team Overview']: Size={len(team_members)}")
        
        for i, member in enumerate(team_members, 1):
            print(f"    {i}. {member['Name']:<20} | {member['Role']:<22} | {member['Experience']:>2} yrs")
        print()


def display_similarity_scores(df, skill_matrix, projects_list):
    """
    Display detailed similarity scores for project assignments.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Skill matrix
        list: Project list
    """
    print_section("SIMILARITY SCORES & RANKINGS")
    
    for project in projects_list:
        if not project.assigned_team:
            continue
        
        # Generate ranking for this project
        ranking = rank_employees_by_similarity(df, skill_matrix, project, project.name)
        
        print(f"\n{project.project_id} | {project.name}")
        print(f"{'Rank':<6} {'Name':<20} {'Skill Sim':<12} {'Exp Score':<12} {'Overall':<12}")
        print(f"{'-' * 62}")
        
        assigned_names = {member['Name'] for member in project.assigned_team}
        
        # Show top 10 and highlight assigned members
        top_n = min(10, len(ranking))
        for i in range(top_n):
            row = ranking.iloc[i]
            name = row['Name']
            marker = "[ASSIGNED]" if name in assigned_names else ""
            print(f"{row['Rank']:<6} {name:<20} {row['Skill_Similarity']:>10.4f}   "
                  f"{row['Experience']/df['Experience'].max():>10.4f}   {row['Overall_Score']:>10.4f}  {marker}")
        
        print()


def display_comprehensive_hr_dashboard(df, skill_matrix, df_assigned, cluster_labels, projects_list):
    """
    Display comprehensive HR dashboard with all analytics.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Skill matrix
        pd.DataFrame: Assigned data
        np.ndarray: Cluster labels
        list: Project list
    """
    print_header("COMPREHENSIVE HR DASHBOARD", "=")
    
    # View 1: Team Distribution
    display_team_distribution(df_assigned, cluster_labels)
    
    # View 2: Employee Workload
    display_employee_workload(df_assigned, projects_list)
    
    # View 3: Skill Gaps
    display_skill_gaps(skill_matrix, projects_list, df)
    
    # View 4: Project-Team Mapping
    display_project_team_mapping(df_assigned, projects_list)
    
    # View 5: Similarity Scores
    display_similarity_scores(df, skill_matrix, projects_list)
    
    # Summary statistics
    print_section("DASHBOARD SUMMARY STATISTICS")
    print(f"  Total Employees: {len(df)}")
    print(f"  Assigned to Projects: {len(df_assigned[df_assigned['Project'].notna()])}")
    print(f"  Unassigned: {len(df_assigned[df_assigned['Project'].isna()])}")
    print(f"  Total Teams: {len(np.unique(cluster_labels))}")
    print(f"  Total Projects: {len([p for p in projects_list if p.assigned_team])}")
    print(f"  Skill Dimensions: {len(CONFIG['SKILLS'])}")
    print()


# ============================================================================
# VISUALIZATION MODULE - TEAM & CLUSTER VISUALIZATION
# ============================================================================

def visualize_team_distribution(df_assigned, cluster_labels):
    """
    Create pie chart showing team distribution.
    
    Args:
        pd.DataFrame: Employee data with assignments
        np.ndarray: Cluster labels
    """
    cluster_counts = pd.Series(cluster_labels).value_counts().sort_index()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Pie Chart
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA502', '#2ECC71', '#9B59B6']
    ax1.pie(cluster_counts.values, labels=[f'Team {i}' for i in cluster_counts.index],
            autopct='%1.1f%%', colors=colors[:len(cluster_counts)], startangle=90)
    ax1.set_title('Team Distribution (Pie Chart)', fontsize=14, fontweight='bold')
    
    # Bar Chart
    ax2.bar([f'Team {i}' for i in cluster_counts.index], cluster_counts.values, 
            color=colors[:len(cluster_counts)], edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Number of Employees', fontsize=11, fontweight='bold')
    ax2.set_title('Team Size Distribution (Bar Chart)', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    for i, v in enumerate(cluster_counts.values):
        ax2.text(i, v + 5, str(v), ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('01_team_distribution.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 01_team_distribution.png")
    plt.close()


def visualize_salary_by_team(df, cluster_labels):
    """
    Create box plot showing performance distribution by team.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Cluster labels
    """
    df_temp = df.copy()
    df_temp['Team'] = cluster_labels
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    teams = sorted(df_temp['Team'].unique())
    perf_by_team = [df_temp[df_temp['Team'] == team]['Performance Rating'].values for team in teams]
    
    bp = ax.boxplot(perf_by_team, labels=[f'Team {t}' for t in teams],
                    patch_artist=True, showmeans=True)
    
    # Color boxes
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA502']
    for patch, color in zip(bp['boxes'], colors[:len(teams)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_ylabel('Performance Rating', fontsize=11, fontweight='bold')
    ax.set_xlabel('Team', fontsize=11, fontweight='bold')
    ax.set_title('Performance Distribution by Team', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add statistics
    for i, team in enumerate(teams):
        team_perf = df_temp[df_temp['Team'] == team]['Performance Rating']
        mean_perf = team_perf.mean()
        ax.text(i+1, mean_perf, f'{mean_perf:.2f}', ha='center', va='bottom',
                fontweight='bold', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('02_performance_by_team.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 02_performance_by_team.png")
    plt.close()


def visualize_experience_by_team(df, cluster_labels):
    """
    Create violin plot showing experience distribution by team.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Cluster labels
    """
    df_temp = df.copy()
    df_temp['Team'] = cluster_labels
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    teams = sorted(df_temp['Team'].unique())
    experience_by_team = [df_temp[df_temp['Team'] == team]['Experience'].values for team in teams]
    
    parts = ax.violinplot(experience_by_team, positions=range(len(teams)),
                          showmeans=True, showmedians=True)
    
    ax.set_xticks(range(len(teams)))
    ax.set_xticklabels([f'Team {t}' for t in teams])
    ax.set_ylabel('Experience (Years)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Team', fontsize=11, fontweight='bold')
    ax.set_title('Experience Distribution by Team', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('03_experience_by_team.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 03_experience_by_team.png")
    plt.close()


def visualize_skill_matrix(skill_matrix):
    """
    Create heatmap of skill matrix (sample of employees x skills).
    
    Args:
        np.ndarray: Skill matrix (employees x skills)
    """
    # Sample 30 employees for visualization
    sample_size = min(30, skill_matrix.shape[0])
    sample_indices = np.random.choice(skill_matrix.shape[0], sample_size, replace=False)
    skill_sample = skill_matrix[sample_indices, :]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    im = ax.imshow(skill_sample, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    
    ax.set_xticks(range(len(CONFIG['SKILLS'])))
    ax.set_xticklabels(CONFIG['SKILLS'], rotation=45, ha='right')
    ax.set_yticks(range(sample_size))
    ax.set_yticklabels([f'Emp {i}' for i in range(sample_size)])
    
    ax.set_xlabel('Skills', fontsize=11, fontweight='bold')
    ax.set_ylabel('Employees (Sample)', fontsize=11, fontweight='bold')
    ax.set_title('Skill Matrix Heatmap (Red=Low, Green=High)', fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Skill Level', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('04_skill_matrix_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 04_skill_matrix_heatmap.png")
    plt.close()


def visualize_project_assignments(df, projects_list):
    """
    Create stacked bar chart showing projects and team assignments.
    
    Args:
        pd.DataFrame: Employee data
        list: Projects with assignments
    """
    project_names = []
    team_sizes = []
    avg_performance = []
    match_scores = []
    
    for project in projects_list:
        if project.assigned_team:
            project_names.append(project.name[:20])  # Truncate long names
            team_sizes.append(len(project.assigned_team))
            if project.assigned_team:
                perf_vals = [m.get('Performance Rating', 0) for m in project.assigned_team]
                avg_perf = sum(perf_vals) / max(1, len(perf_vals))
            else:
                avg_perf = 0
            avg_performance.append(avg_perf)
            match_scores.append(project.match_score)
    
    if not project_names:
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Subplot 1: Team Size
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA502']
    ax1.bar(project_names, team_sizes, color=colors[:len(project_names)], edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Team Size (Members)', fontsize=10, fontweight='bold')
    ax1.set_title('Assigned Team Size per Project', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    for i, v in enumerate(team_sizes):
        ax1.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
    
    # Subplot 2: Avg Performance
    ax2.bar(project_names, avg_performance, color=colors[:len(project_names)], edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Avg Performance Rating', fontsize=10, fontweight='bold')
    ax2.set_title('Average Performance per Project', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    for i, v in enumerate(avg_performance):
        ax2.text(i, v + 0.1, f'{v:.2f}', ha='center', fontweight='bold', fontsize=8)
    
    # Subplot 3: Match Score
    ax3.bar(project_names, match_scores, color=colors[:len(project_names)], edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Match Score', fontsize=10, fontweight='bold')
    ax3.set_ylim([0, 100])
    ax3.set_title('Team-Project Match Quality Score', fontsize=12, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    for i, v in enumerate(match_scores):
        ax3.text(i, v + 1, f'{v:.1f}', ha='center', fontweight='bold')
    
    # Subplot 4: Summary Table
    ax4.axis('off')
    summary_data = []
    for pname, size, avg_perf, score in zip(project_names, team_sizes, avg_performance, match_scores):
        summary_data.append([pname, f'{size}', f'{avg_perf:.2f}', f'{score:.1f}/100'])
    
    table = ax4.table(cellText=summary_data, 
                     colLabels=['Project', 'Team Size', 'Avg Performance', 'Match Score'],
                     cellLoc='center', loc='center', 
                     colColours=['#E8E8E8']*4)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    ax4.set_title('Project Assignment Summary', fontsize=12, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('05_project_assignments.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 05_project_assignments.png")
    plt.close()


def visualize_skill_gaps(skill_matrix, projects_list, df):
    """
    Create heatmap showing skill coverage per project.
    
    Args:
        np.ndarray: Skill matrix
        list: Projects
        pd.DataFrame: Employee data
    """
    skill_gaps = []
    project_names = []
    
    for project in projects_list:
        if not project.assigned_team:
            continue
        
        assigned_names = [member['Name'] for member in project.assigned_team]
        assigned_indices = df[df['Name'].isin(assigned_names)].index.tolist()
        
        required_skills = list(project.priority_skills.keys())
        project_gaps = []
        
        for skill in CONFIG['SKILLS']:
            if skill in required_skills:
                if assigned_indices:
                    coverage = skill_matrix[assigned_indices, CONFIG['SKILLS'].index(skill)].mean()
                else:
                    coverage = 0
                gap = 1.0 - coverage
                project_gaps.append(gap * 100)  # Convert to percentage
            else:
                project_gaps.append(0)  # Not required
        
        skill_gaps.append(project_gaps)
        project_names.append(project.name[:15])
    
    if not skill_gaps:
        return
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    im = ax.imshow(skill_gaps, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=100)
    
    ax.set_xticks(range(len(CONFIG['SKILLS'])))
    ax.set_xticklabels(CONFIG['SKILLS'], rotation=45, ha='right')
    ax.set_yticks(range(len(project_names)))
    ax.set_yticklabels(project_names)
    
    ax.set_xlabel('Skills', fontsize=11, fontweight='bold')
    ax.set_ylabel('Projects', fontsize=11, fontweight='bold')
    ax.set_title('Skill Gap Analysis by Project (% Gap, Red=High Gap)', fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Gap (%)', fontsize=10, fontweight='bold')
    
    # Add gap percentages
    for i in range(len(project_names)):
        for j in range(len(CONFIG['SKILLS'])):
            if skill_gaps[i][j] > 0:
                text = ax.text(j, i, f'{skill_gaps[i][j]:.0f}%',
                             ha="center", va="center", color="black", fontsize=8)
    
    plt.tight_layout()
    plt.savefig('06_skill_gaps_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 06_skill_gaps_heatmap.png")
    plt.close()


def visualize_clustering_metrics(eval_results):
    """
    Create line plots for clustering evaluation metrics.
    
    Args:
        list: Evaluation results with K values and metrics
    """
    k_values = [r['k'] for r in eval_results]
    silhouette_scores = [r['silhouette'] for r in eval_results]
    calinski_scores = [r['calinski'] for r in eval_results]
    
    # Normalize Calinski scores to similar scale
    calinski_normalized = np.array(calinski_scores) / np.max(calinski_scores)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Silhouette Score
    ax1.plot(k_values, silhouette_scores, marker='o', linewidth=2, markersize=8, color='#FF6B6B')
    ax1.scatter(k_values, silhouette_scores, color='#FF6B6B', s=100, zorder=5)
    ax1.set_xlabel('Number of Clusters (K)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Silhouette Score', fontsize=11, fontweight='bold')
    ax1.set_title('K-Means Clustering: Silhouette Score', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(k_values)
    
    # Mark best K
    best_k_idx = np.argmax(silhouette_scores)
    ax1.scatter([k_values[best_k_idx]], [silhouette_scores[best_k_idx]], 
               color='gold', s=300, marker='*', zorder=10, label=f'Best K={k_values[best_k_idx]}')
    ax1.legend(fontsize=10)
    
    # Calinski-Harabasz Index (normalized)
    ax2.plot(k_values, calinski_normalized, marker='s', linewidth=2, markersize=8, color='#4ECDC4')
    ax2.scatter(k_values, calinski_normalized, color='#4ECDC4', s=100, zorder=5)
    ax2.set_xlabel('Number of Clusters (K)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Calinski-Harabasz Score (Normalized)', fontsize=11, fontweight='bold')
    ax2.set_title('K-Means Clustering: Calinski-Harabasz Index', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(k_values)
    
    # Mark best K
    best_k_idx_ch = np.argmax(calinski_normalized)
    ax2.scatter([k_values[best_k_idx_ch]], [calinski_normalized[best_k_idx_ch]], 
               color='gold', s=300, marker='*', zorder=10, label=f'Best K={k_values[best_k_idx_ch]}')
    ax2.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig('07_clustering_metrics.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 07_clustering_metrics.png")
    plt.close()


def visualize_employee_scatter(df, cluster_labels, skill_matrix):
    """
    Create scatter plots of employees by various features, colored by cluster.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Cluster labels
        np.ndarray: Skill matrix
    """
    df_temp = df.copy()
    df_temp['Cluster'] = cluster_labels
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    clusters = sorted(df_temp['Cluster'].unique())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA502']
    
    # Plot 1: Performance vs Experience
    for i, cluster in enumerate(clusters):
        cluster_data = df_temp[df_temp['Cluster'] == cluster]
        ax1.scatter(cluster_data['Experience'], cluster_data['Performance Rating'], 
                   label=f'Team {cluster}', color=colors[i % len(colors)], 
                   s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    ax1.set_xlabel('Experience (Years)', fontsize=10, fontweight='bold')
    ax1.set_ylabel('Performance Rating', fontsize=10, fontweight='bold')
    ax1.set_title('Employee Positioning: Performance vs Experience', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Skill Level vs Experience
    for i, cluster in enumerate(clusters):
        cluster_data = df_temp[df_temp['Cluster'] == cluster]
        ax2.scatter(cluster_data['Experience'], cluster_data['Skill Level'], 
                   label=f'Team {cluster}', color=colors[i % len(colors)], 
                   s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    ax2.set_xlabel('Experience (Years)', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Skill Level', fontsize=10, fontweight='bold')
    ax2.set_title('Employee Positioning: Skill Level vs Experience', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Skill Level vs Performance
    for i, cluster in enumerate(clusters):
        cluster_data = df_temp[df_temp['Cluster'] == cluster]
        ax3.scatter(cluster_data['Skill Level'], cluster_data['Performance Rating'], 
                   label=f'Team {cluster}', color=colors[i % len(colors)], 
                   s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    ax3.set_xlabel('Skill Level', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Performance Rating', fontsize=10, fontweight='bold')
    ax3.set_title('Employee Positioning: Skill Level vs Performance', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Availability vs Experience
    for i, cluster in enumerate(clusters):
        cluster_mask = df_temp['Cluster'] == cluster
        ax4.scatter(df_temp[cluster_mask]['Experience'], df_temp[cluster_mask]['Availability Score'], 
                   label=f'Team {cluster}', color=colors[i % len(colors)], 
                   s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    ax4.set_xlabel('Experience (Years)', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Availability Score', fontsize=10, fontweight='bold')
    ax4.set_title('Employee Positioning: Availability vs Experience', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('08_employee_scatter_plots.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 08_employee_scatter_plots.png")
    plt.close()


def visualize_gender_distribution(df, cluster_labels):
    """
    Create bar charts showing category distribution per team.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Cluster labels
    """
    df_temp = df.copy()
    df_temp['Cluster'] = cluster_labels
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    clusters = sorted(df_temp['Cluster'].unique())
    categories = sorted(df_temp['Category'].unique())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA502', '#2ECC71', '#9B59B6']
    
    x_labels = [f'Team {c}' for c in clusters]
    bottom_counts = np.zeros(len(clusters))
    for i, category in enumerate(categories):
        counts = []
        for cluster in clusters:
            cluster_data = df_temp[df_temp['Cluster'] == cluster]
            counts.append((cluster_data['Category'] == category).sum())
        axes[0].bar(
            x_labels,
            counts,
            bottom=bottom_counts,
            label=category,
            color=colors[i % len(colors)],
            alpha=0.85
        )
        bottom_counts += np.array(counts)
    
    axes[0].set_ylabel('Number of Employees', fontsize=10, fontweight='bold')
    axes[0].set_title('Category Distribution by Team (Stacked)', fontsize=12, fontweight='bold')
    axes[0].legend(fontsize=9)
    axes[0].grid(axis='y', alpha=0.3)
    
    # Percentages
    bottom_pct = np.zeros(len(clusters))
    for i, category in enumerate(categories):
        percentages = []
        for cluster in clusters:
            cluster_data = df_temp[df_temp['Cluster'] == cluster]
            total = len(cluster_data)
            pct = (cluster_data['Category'] == category).sum() / max(1, total) * 100
            percentages.append(pct)
        axes[1].bar(
            x_labels,
            percentages,
            bottom=bottom_pct,
            label=category,
            color=colors[i % len(colors)],
            alpha=0.85
        )
        bottom_pct += np.array(percentages)
    
    axes[1].set_ylabel('Percentage (%)', fontsize=10, fontweight='bold')
    axes[1].set_title('Category Distribution by Team (Percentage)', fontsize=12, fontweight='bold')
    axes[1].legend(fontsize=9)
    axes[1].set_ylim([0, 100])
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('09_category_distribution.png', dpi=300, bbox_inches='tight')
    print(f"  [SAVED] Visualization: 09_category_distribution.png")
    plt.close()


def generate_all_visualizations(df, skill_matrix, df_assigned, cluster_labels, 
                                projects_list, eval_results):
    """
    Generate all visualizations in sequence.
    
    Args:
        pd.DataFrame: Employee data
        np.ndarray: Skill matrix
        pd.DataFrame: Assigned employee data
        np.ndarray: Cluster labels
        list: Projects list
        list: Evaluation results
    """
    print_section("VISUALIZATION MODULE: GENERATING CHARTS & GRAPHS")
    
    print("  Generating visualizations (saving as PNG files)...\n")
    
    try:
        visualize_team_distribution(df_assigned, cluster_labels)
        visualize_salary_by_team(df, cluster_labels)
        visualize_experience_by_team(df, cluster_labels)
        visualize_skill_matrix(skill_matrix)
        visualize_project_assignments(df, projects_list)
        visualize_skill_gaps(skill_matrix, projects_list, df)
        visualize_clustering_metrics(eval_results)
        visualize_employee_scatter(df, cluster_labels, skill_matrix)
        visualize_gender_distribution(df, cluster_labels)
        
        print("\n  All visualizations generated successfully!")
        print(f"  [SAVED] 9 PNG visualization files created in current directory")
        
    except Exception as e:
        print(f"  [WARNING] Error generating visualizations: {str(e)}")


# ============================================================================


def main():
    """Execute complete AI-powered team formation pipeline."""
    
    print("\n")
    print_header("AI-POWERED SKILL-BASED TEAM FORMATION SYSTEM", "=")
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Step 1: Load Data
        df, csv_path = load_employee_data()
        
        # Step 2: Preprocess Data
        df_clean, encoders = preprocess_data(df)
        
        # Step 3: Feature Engineering
        df_features = engineer_features(df_clean)
        
        # Step 4: Select & Scale Features
        features_list = build_feature_list(df_features)
        X_scaled, scaler = select_and_scale_features(df_features, features_list)
        
        # ðŸŽ¯ NEW: Display Scaling Basis
        display_feature_scaling_basis(scaler, features_list)
        
        # Step 5: Compute Attention Weights
        attention_weights, weight_stats = compute_attention_weights(X_scaled, features_list)
        
        # ðŸŽ¯ NEW: Display Clustering Parameters
        display_clustering_parameters(df_features, attention_weights, weight_stats, features_list)
        
        # Apply attention weights
        X_weighted = X_scaled * attention_weights
        
        # PHASE 1: ATTENTION-BASED SKILL WEIGHTING
        print_header("PHASE 1: ATTENTION-BASED SKILL WEIGHTING")
        skill_matrix = define_employee_skills(df_features)
        
        # Step 6: Find Optimal K
        optimal_k, eval_results = find_optimal_clusters(
            X_weighted,
            CONFIG['MIN_CLUSTERS'],
            CONFIG['MAX_CLUSTERS']
        )
        
        # ðŸŽ¯ NEW: Display Team Formation Logic
        display_team_formation_logic(optimal_k, eval_results)
        
        # Step 7: Perform Final Clustering
        cluster_labels, kmeans_model = perform_final_clustering(X_weighted, optimal_k)
        
        # Step 8: Analyze & Display Results
        analyze_and_display_teams(df_features, cluster_labels)
        
        # Step 9: Define Projects and Assign Teams
        print_header("STEP 9: PROJECT ASSIGNMENT & TEAM MATCHING")
        
        # Define sample projects with requirements
        projects = [
            ProjectRequirement(
                project_id="PROJ001",
                name="Mobile App Development",
                required_team_size=5,
                min_experience=3,
                max_budget=200000,
                priority_skills={'frontend': 0.4, 'backend': 0.3, 'testing': 0.3},
                deadline_days=45
            ),
            ProjectRequirement(
                project_id="PROJ002",
                name="Data Analytics Platform",
                required_team_size=4,
                min_experience=4,
                max_budget=180000,
                priority_skills={'data_science': 0.5, 'databases': 0.3, 'analytics': 0.2},
                deadline_days=30
            ),
            ProjectRequirement(
                project_id="PROJ003",
                name="Cloud Infrastructure",
                required_team_size=3,
                min_experience=5,
                max_budget=150000,
                priority_skills={'leadership': 0.4, 'devops': 0.4, 'security': 0.2},
                deadline_days=60
            ),
            ProjectRequirement(
                project_id="PROJ004",
                name="Web Portal Redesign",
                required_team_size=4,
                min_experience=2,
                max_budget=160000,
                priority_skills={'frontend': 0.5, 'ux_design': 0.3, 'testing': 0.2},
                deadline_days=35
            )
        ]
        
        # Assign teams to projects
        projects_with_teams, df_assigned = assign_teams_to_project(
            df_features, cluster_labels, projects
        )
        
        # Display project assignments
        display_project_assignments(projects_with_teams, df_assigned)
        
        # Display project summary
        display_project_summary(projects_with_teams)
        
        # PHASE 2: COMPREHENSIVE HR DASHBOARD
        print_header("PHASE 2: COMPREHENSIVE HR DASHBOARD")
        display_comprehensive_hr_dashboard(df_features, skill_matrix, df_assigned, cluster_labels, projects_with_teams)
        
        # PHASE 3: VISUALIZATION MODULE
        print_header("PHASE 3: VISUALIZATION & CHARTS")
        generate_all_visualizations(df_features, skill_matrix, df_assigned, cluster_labels, 
                                   projects_with_teams, eval_results)
        
        # Summary
        print_header("EXECUTION SUMMARY", "=")
        print(f"[OK] Pipeline Completed Successfully")
        print(f"[OK] Teams Formed: {optimal_k}")
        print(f"[OK] Total Employees Processed: {len(df_features)}")
        print(f"[OK] Silhouette Score: {max(eval_results, key=lambda x: x['silhouette'])['silhouette']:.4f}")
        print(f"[OK] Projects Assigned: {sum(1 for p in projects_with_teams if p.assigned_team)}")
        print(f"[OK] Total Employees Assigned to Projects: {len(df_assigned[df_assigned['Project'].notna()])}")
        print(f"[OK] Visualizations Generated: 9 PNG files")
        print(f"\n  Visualizations Created:")
        print(f"    1. team_distribution.png - Team size pie/bar charts")
        print(f"    2. performance_by_team.png - Performance distribution by team")
        print(f"    3. experience_by_team.png - Experience distribution by team")
        print(f"    4. skill_matrix_heatmap.png - Employee skills heatmap")
        print(f"    5. project_assignments.png - Project team assignments")
        print(f"    6. skill_gaps_heatmap.png - Skill gaps by project")
        print(f"    7. clustering_metrics.png - K-Means evaluation metrics")
        print(f"    8. employee_scatter_plots.png - 4 scatter plot perspectives")
        print(f"    9. category_distribution.png - Category breakdown per team")
        print(f"\n  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

