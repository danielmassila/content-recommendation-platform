package com.services;


import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.model.User;
import com.example.reco.repositories.UserRepository;
import com.example.reco.services.UserServiceImpl;
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

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrowsExactly;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class UserServiceImplTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserServiceImpl userService;

    @Test
    void shouldReturnUserIfExists() {
        // mock user
        User user = new User();
        user.setEmail("email@test");
        user.setId(1L);
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));

        // simulate
        var response = userService.getUserById(1L);

        // check the return
        assertEquals(1L, response.getId());
        assertEquals("email@test", response.getEmail());
        verify(userRepository).findById(1L);

    }

    @Test
    void shouldThrowExceptionIfUserNotFound() {

        when(userRepository.findById(10L)).thenReturn(Optional.empty());

        assertThrowsExactly(NotFoundException.class, () -> userService.getUserById(10L), "User with id" + 10L + " not found");
        verify(userRepository).findById(10L);
    }

    @Test
    void shouldReturnEmptyWhenEmptyUsersTable() {

        when(userRepository.findAll(any(Pageable.class))).thenReturn(Page.empty());

        var response = userService.getAllUsers(50);

        assertNotNull(response);
        assertEquals(0, response.size());
        verify(userRepository).findAll(any(Pageable.class));

    }

    @Test
    void shouldReturnMappedUsersWhenRepositoryReturnsUsers() {

        // mock several users
        User user1 = new User();
        user1.setEmail("user1@test");
        user1.setId(1L);

        User user2 = new User();
        user2.setEmail("user2@test");
        user2.setId(2L);

        when(userRepository.findAll(any(Pageable.class))).thenReturn(new PageImpl<>(List.of(user1, user2)));

        var response = userService.getAllUsers(10);

        assertNotNull(response);
        assertEquals(2, response.size());
        assertEquals(1L, response.get(0).getId());
        assertEquals("user1@test", response.get(0).getEmail());
        assertEquals(2L, response.get(1).getId());
        assertEquals("user2@test", response.get(1).getEmail());
        verify(userRepository).findAll(any(Pageable.class));

    }

    @Test
    void shouldCapUsersLimitWhenLimitIsTooHigh() {

        // we test HOW the repository is called, not the result
        when(userRepository.findAll(any(Pageable.class))).thenReturn(Page.empty());

        userService.getAllUsers(99999);

        // we capture the argument that was used when calling the repository
        ArgumentCaptor<Pageable> argumentCaptor = ArgumentCaptor.forClass(Pageable.class);

        verify(userRepository).findAll(argumentCaptor.capture());
        Pageable pageableUsed = argumentCaptor.getValue();

        assertEquals(0, pageableUsed.getPageNumber());
        assertEquals(50, pageableUsed.getPageSize());

    }

    @Test
    void shouldUseUsersDefaultLimitIfLimitInvalid() {
        when(userRepository.findAll(any(Pageable.class))).thenReturn(Page.empty());

        userService.getAllUsers(-1);

        ArgumentCaptor<Pageable> argumentCaptor = ArgumentCaptor.forClass(Pageable.class);
        verify(userRepository).findAll(argumentCaptor.capture());

        Pageable pageableUsed = argumentCaptor.getValue();

        assertEquals(0, pageableUsed.getPageNumber());
        assertEquals(50, pageableUsed.getPageSize()); // default limit

    }

}
