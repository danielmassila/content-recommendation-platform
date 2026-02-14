package com.example.reco.config;

import com.example.reco.model.Item;
import com.example.reco.model.ItemType;
import com.example.reco.model.Rating;
import com.example.reco.model.User;
import com.example.reco.repositories.ItemRepository;
import com.example.reco.repositories.RatingRepository;
import com.example.reco.repositories.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

@Component
public class SmokeTestRunner implements CommandLineRunner {

    private final UserRepository users;
    private final ItemRepository items;
    private final RatingRepository ratings;

    public SmokeTestRunner(UserRepository users,
                           ItemRepository items,
                           RatingRepository ratings) {
        this.users = users;
        this.items = items;
        this.ratings = ratings;
    }

    @Override
    public void run(String... args) {
        User u = users.save(new User("user@test.com", "hash"));
        Item i = items.save(new Item("Film random", ItemType.MOVIE, "{\"genre\":\"Action\"}"));
        ratings.save(new Rating(u, i, BigDecimal.valueOf(5)));
        System.out.println("Users: " + users.count());
        System.out.println("Items: " + items.count());
        System.out.println("Ratings: " + ratings.count());
    }
}
