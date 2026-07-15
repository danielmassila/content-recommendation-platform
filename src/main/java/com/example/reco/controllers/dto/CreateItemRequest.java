package com.example.reco.controllers.dto;


import com.example.reco.model.ItemType;

public class CreateItemRequest {
    private String title;
    private ItemType type;
    private String metadata;

    public CreateItemRequest() {
    }

    public CreateItemRequest(String title, ItemType type, String metadata) {
        this.title = title;
        this.type = type;
        this.metadata = metadata;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getMetadata() {
        return metadata;
    }

    public void setMetadata(String metadata) {
        this.metadata = metadata;
    }

    public ItemType getType() {
        return type;
    }

    public void setItemType(ItemType type) {
        this.type = type;
    }
}