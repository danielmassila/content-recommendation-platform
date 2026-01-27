package com.services;


import com.example.reco.common.exceptions.NotFoundException;
import com.example.reco.model.User;
import com.example.reco.repositories.UserRepository;
import com.example.reco.services.UserServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrowsExactly;
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

}
