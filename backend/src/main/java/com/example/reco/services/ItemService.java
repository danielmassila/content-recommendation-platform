package com.example.reco.services;

import com.example.reco.controllers.dto.CreateItemRequest;
import com.example.reco.controllers.dto.ItemResponse;
import com.example.reco.controllers.dto.ItemPageResponse;
import com.example.reco.model.ItemType;

public interface ItemService {
    ItemResponse createItem(CreateItemRequest createItemRequest);

    ItemResponse getItemById(Long id);

    ItemPageResponse searchItems(String query, ItemType type, int page, int size);
}
