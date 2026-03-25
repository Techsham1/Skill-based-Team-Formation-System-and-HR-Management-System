package com.hrSystem.HRM.service;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Service
public class MlModelService {

    private final RestTemplate restTemplate;
    private final String mlApiUrl;

    public MlModelService(
            RestTemplateBuilder builder,
            @Value("${ml.api.url:http://localhost:5000/api/ml/team-formation}") String mlApiUrl
    ) {
        this.restTemplate = builder
                .setConnectTimeout(Duration.ofSeconds(5))
                .setReadTimeout(Duration.ofSeconds(30))
                .build();
        this.mlApiUrl = mlApiUrl;
    }

    public JsonNode generateTeam(Map<String, Object> criteria, Map<String, Object> config) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("criteria", criteria != null ? criteria : Map.of());
        payload.put("config", config != null ? config : Map.of());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

        ResponseEntity<JsonNode> response =
                restTemplate.postForEntity(mlApiUrl, request, JsonNode.class);

        return response.getBody();
    }
}
