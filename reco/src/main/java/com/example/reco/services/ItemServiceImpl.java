package com.example.reco.services;

import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.controllers.dto.CreateItemRequest;
import com.example.reco.controllers.dto.ItemResponse;
import com.example.reco.model.Item;
import com.example.reco.repositories.ItemRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class ItemServiceImpl implements ItemService {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 50;

    private ItemRepository itemRepository;

    public ItemServiceImpl(ItemRepository itemRepository) {
        this.itemRepository = itemRepository;
    }

    @Override
    public ItemResponse createItem(CreateItemRequest createItemRequest) {
        Item item = new Item();
        item.setTitle(createItemRequest.getTitle());
        item.setType(createItemRequest.getType());
        item.setMetadata(createItemRequest.getMetadata());
        Item saved = itemRepository.save(item);
        return toResponse(saved);
    }

    @Override
    @Transactional(readOnly = true)
    public ItemResponse getItemById(Long id) {
        Item item = itemRepository.findById(id).orElseThrow(() -> new NotFoundException("Item with id " + id + " not found"));
        return toResponse(item);
    }

    @Override
    @Transactional(readOnly = true)
    public List<ItemResponse> getAllItems(int limit) {
        int myLimit = (limit <= 0) ? DEFAULT_LIMIT : limit;
        myLimit = Math.min(myLimit, MAX_LIMIT);
        List<ItemResponse> itemList = itemRepository.findAll(PageRequest.of(0, myLimit))
                                              .stream()
                                              .map(this::toResponse)
                                              .toList();
        return itemList;
    }

    private ItemResponse toResponse(Item item) {
        return new ItemResponse(
                item.getId(),
                item.getTitle(),
                item.getType(),
                item.getMetadata()
        );
    }
}
