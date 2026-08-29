package com.example.reco.services;

import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.controllers.dto.CreateItemRequest;
import com.example.reco.controllers.dto.ItemResponse;
import com.example.reco.controllers.dto.ItemPageResponse;
import com.example.reco.model.Item;
import com.example.reco.model.ItemType;
import com.example.reco.repositories.ItemRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Page;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class ItemServiceImpl implements ItemService {

    private static final int DEFAULT_SIZE = 20;
    private static final int MAX_SIZE = 50;

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
    public ItemPageResponse searchItems(
            String query,
            ItemType type,
            String genre,
            Integer year,
            Double minVote,
            String ratingStatus,
            Long userId,
            int page,
            int size
    ) {
        int safePage = Math.max(page, 0);
        int safeSize = size <= 0 ? DEFAULT_SIZE : Math.min(size, MAX_SIZE);
        String normalizedQuery = query == null ? "" : query.trim();
        String normalizedGenre = genre == null || genre.equalsIgnoreCase("all") ? "" : genre.trim();
        String normalizedRatingStatus = switch (ratingStatus == null ? "all" : ratingStatus.toLowerCase()) {
            case "rated" -> "rated";
            case "unrated" -> "unrated";
            default -> "all";
        };
        PageRequest pageable = PageRequest.of(safePage, safeSize);

        Page<Item> result = itemRepository.searchCatalog(
                type == null ? "" : type.name(),
                normalizedQuery,
                normalizedGenre,
                year,
                minVote,
                normalizedRatingStatus,
                userId,
                pageable
        );

        return new ItemPageResponse(
                result.getContent().stream().map(this::toResponse).toList(),
                result.getNumber(),
                result.getSize(),
                result.getTotalElements(),
                result.getTotalPages()
        );
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
