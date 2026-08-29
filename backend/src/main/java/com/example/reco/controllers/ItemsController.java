package com.example.reco.controllers;

import com.example.reco.controllers.dto.ItemResponse;
import com.example.reco.controllers.dto.ItemPageResponse;
import com.example.reco.model.ItemType;
import com.example.reco.services.ItemService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

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
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        return itemService.searchItems(query, type, page, size);
    }
}
