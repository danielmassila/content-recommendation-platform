package com.example.reco.services;

import com.example.reco.controllers.dto.CreateItemRequest;
import com.example.reco.controllers.dto.ItemResponse;

import java.util.List;

public interface ItemService {
    ItemResponse createItem(CreateItemRequest createItemRequest);

    ItemResponse getItemById(Long id);

    List<ItemResponse> getAllItems(int limit);
}
