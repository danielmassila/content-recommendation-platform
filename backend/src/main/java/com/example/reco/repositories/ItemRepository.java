package com.example.reco.repositories;

import com.example.reco.model.Item;
import com.example.reco.model.ItemType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ItemRepository extends JpaRepository<Item, Long> {
    Page<Item> findByType(ItemType type, Pageable pageable);

    Page<Item> findByTitleContainingIgnoreCase(String query, Pageable pageable);

    Page<Item> findByTypeAndTitleContainingIgnoreCase(ItemType type, String query, Pageable pageable);
}
