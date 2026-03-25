package com.hrSystem.HRM.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.hrSystem.HRM.service.MlModelService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/ml")
@CrossOrigin(origins = "*")
public class MlModelController {

    private final MlModelService mlModelService;

    @Autowired
    public MlModelController(MlModelService mlModelService) {
        this.mlModelService = mlModelService;
    }

    @PostMapping("/team-formation")
    public ResponseEntity<JsonNode> generateTeam(@RequestBody Map<String, Object> payload) {
        Map<String, Object> criteria = getMap(payload, "criteria");
        Map<String, Object> config = getMap(payload, "config");

        JsonNode result = mlModelService.generateTeam(criteria, config);
        return ResponseEntity.ok(result);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> getMap(Map<String, Object> payload, String key) {
        if (payload == null) {
            return Map.of();
        }
        Object value = payload.get(key);
        if (value instanceof Map<?, ?> mapValue) {
            return (Map<String, Object>) mapValue;
        }
        return Map.of();
    }
}
