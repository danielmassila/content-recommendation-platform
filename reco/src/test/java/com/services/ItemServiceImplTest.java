package com.services;

import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.controllers.dto.CreateItemRequest;
import com.example.reco.controllers.dto.ItemResponse;
import com.example.reco.model.Item;
import com.example.reco.model.ItemType;
import com.example.reco.repositories.ItemRepository;
import com.example.reco.services.ItemServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ItemServiceImplTest {

    @Mock
    private ItemRepository itemRepository;

    @InjectMocks
    private ItemServiceImpl itemService;

    @Test
    void shouldReturnItemIfExists() {
        Item item = new Item();
        item.setId(1L);
        item.setTitle("Titanic");
        item.setType(ItemType.MOVIE);
        item.setMetadata("{\"producer\":\"James Cameron\"}");

        when(itemRepository.findById(1L)).thenReturn(Optional.of(item));

        ItemResponse response = itemService.getItemById(1L);

        assertNotNull(response);
        assertEquals(1L, response.getId());
        assertEquals("Titanic", response.getTitle());
        assertEquals(ItemType.MOVIE, response.getItemType());
        assertEquals("{\"producer\":\"James Cameron\"}", response.getMetadata());

        verify(itemRepository).findById(1L);
    }

    @Test
    void shouldThrowExceptionIfItemNotFound() {
        when(itemRepository.findById(10L)).thenReturn(Optional.empty());

        assertThrowsExactly(NotFoundException.class, () -> itemService.getItemById(10L));

        verify(itemRepository).findById(10L);
    }

    @Test
    void shouldReturnEmptyWhenEmptyItemsTable() {
        when(itemRepository.findAll(any(Pageable.class))).thenReturn(Page.empty());

        var response = itemService.getAllItems(50);

        assertNotNull(response);
        assertTrue(response.isEmpty());
        verify(itemRepository).findAll(any(Pageable.class));
    }

    @Test
    void shouldReturnMappedItemsWhenRepositoryReturnsItems() {
        Item item1 = new Item();
        item1.setId(1L);
        item1.setTitle("Item 1");
        item1.setType(ItemType.MOVIE);
        item1.setMetadata("{\"a\":1}");

        Item item2 = new Item();
        item2.setId(2L);
        item2.setTitle("Item 2");
        item2.setType(ItemType.MOVIE);
        item2.setMetadata("{\"b\":2}");

        when(itemRepository.findAll(any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(item1, item2)));

        var response = itemService.getAllItems(10);

        assertNotNull(response);
        assertEquals(2, response.size());

        assertEquals(1L, response.get(0).getId());
        assertEquals("Item 1", response.get(0).getTitle());
        assertEquals(ItemType.MOVIE, response.get(0).getItemType());
        assertEquals("{\"a\":1}", response.get(0).getMetadata());

        assertEquals(2L, response.get(1).getId());
        assertEquals("Item 2", response.get(1).getTitle());
        assertEquals(ItemType.MOVIE, response.get(1).getItemType());
        assertEquals("{\"b\":2}", response.get(1).getMetadata());

        verify(itemRepository).findAll(any(Pageable.class));
    }

    @Test
    void shouldCapItemsLimitWhenLimitIsTooHigh() {
        when(itemRepository.findAll(any(Pageable.class))).thenReturn(Page.empty());

        itemService.getAllItems(99999);

        ArgumentCaptor<Pageable> captor = ArgumentCaptor.forClass(Pageable.class);
        verify(itemRepository).findAll(captor.capture());

        Pageable pageableUsed = captor.getValue();
        assertEquals(0, pageableUsed.getPageNumber());
        assertEquals(50, pageableUsed.getPageSize());
    }

    @Test
    void shouldUseItemsDefaultLimitIfLimitInvalid() {
        when(itemRepository.findAll(any(Pageable.class))).thenReturn(Page.empty());

        itemService.getAllItems(-1);

        ArgumentCaptor<Pageable> captor = ArgumentCaptor.forClass(Pageable.class);
        verify(itemRepository).findAll(captor.capture());

        Pageable pageableUsed = captor.getValue();
        assertEquals(0, pageableUsed.getPageNumber());
        assertEquals(50, pageableUsed.getPageSize());
    }

    @Test
    void shouldCreateNewItem() {
        CreateItemRequest req = new CreateItemRequest();
        req.setTitle("Dune");
        req.setItemType(ItemType.MOVIE);
        req.setMetadata("{\"year\":\"2021\"}");

        when(itemRepository.save(any(Item.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        ItemResponse response = itemService.createItem(req);

        ArgumentCaptor<Item> itemCaptor = ArgumentCaptor.forClass(Item.class);
        verify(itemRepository).save(itemCaptor.capture());

        Item saved = itemCaptor.getValue();
        assertEquals("Dune", saved.getTitle());
        assertEquals(ItemType.MOVIE, saved.getType());
        assertEquals("{\"year\":\"2021\"}", saved.getMetadata());

        assertNotNull(response);
        assertEquals("Dune", response.getTitle());
        assertEquals(ItemType.MOVIE, response.getItemType());
        assertEquals("{\"year\":\"2021\"}", response.getMetadata());
    }
}
