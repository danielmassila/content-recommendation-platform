package com.example.reco.controllers.dto;

import com.example.reco.model.ItemType;


public class ItemResponse {
    private Long id;
    private String title;
    private ItemType itemType;
    private String metadata;

    public ItemResponse(Long id, String title, ItemType itemType, String metadata) {
        this.id = id;
        this.title = title;
        this.itemType = itemType;
        this.metadata = metadata;
    }

    public Long getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public ItemType getItemType() {
        return itemType;
    }

    public String getMetadata() {
        return metadata;
    }
}


