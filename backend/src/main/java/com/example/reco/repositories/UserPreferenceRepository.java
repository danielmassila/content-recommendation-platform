package com.example.reco.repositories;

import com.example.reco.model.UserPreference;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserPreferenceRepository extends JpaRepository<UserPreference, Long> {
    List<UserPreference> findByUserIdOrderByCreatedAtAsc(Long userId);

    void deleteByUserId(Long userId);
}
