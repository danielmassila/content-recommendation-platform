package com.example.reco.controllers.dto;

import java.util.List;

public record ItemPageResponse(
        List<ItemResponse> items,
        int page,
        int size,
        long totalItems,
        int totalPages
) {
}
