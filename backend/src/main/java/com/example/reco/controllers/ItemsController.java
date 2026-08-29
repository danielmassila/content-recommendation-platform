package com.example.reco.controllers;

import com.example.reco.auth.AuthenticatedUser;
import com.example.reco.controllers.dto.ItemResponse;
import com.example.reco.controllers.dto.ItemPageResponse;
import com.example.reco.model.ItemType;
import com.example.reco.services.ItemService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.security.core.annotation.AuthenticationPrincipal;

@RestController
@RequestMapping("/api/v1/items")
public class ItemsController {

    private final ItemService itemService;

    public ItemsController(ItemService itemService) {
        this.itemService = itemService;
    }

    @GetMapping("/{id}")
    public ItemResponse getItemById(@PathVariable Long id) {
        return itemService.getItemById(id);
    }

    @GetMapping
    public ItemPageResponse getAllItems(
            @RequestParam(defaultValue = "") String query,
            @RequestParam(required = false) ItemType type,
            @RequestParam(defaultValue = "") String genre,
            @RequestParam(required = false) Integer year,
            @RequestParam(required = false) Double minVote,
            @RequestParam(defaultValue = "all") String ratingStatus,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @AuthenticationPrincipal AuthenticatedUser principal
    ) {
        return itemService.searchItems(
                query,
                type,
                genre,
                year,
                minVote,
                ratingStatus,
                principal == null ? null : principal.id(),
                page,
                size
        );
    }
}
