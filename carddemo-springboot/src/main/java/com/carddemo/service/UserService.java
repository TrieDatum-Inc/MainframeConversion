package com.carddemo.service;

import com.carddemo.dto.UserCreateRequest;
import com.carddemo.dto.UserDto;
import com.carddemo.dto.UserUpdateRequest;
import com.carddemo.entity.User;
import com.carddemo.exception.BadRequestException;
import com.carddemo.exception.ResourceNotFoundException;
import com.carddemo.repository.UserRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    public Page<UserDto> listUsers(Pageable pageable) {
        return userRepository.findAll(pageable).map(UserDto::fromEntity);
    }

    public UserDto getUser(String userId) {
        User user = userRepository.findById(userId.toUpperCase())
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));
        return UserDto.fromEntity(user);
    }

    @Transactional
    public UserDto createUser(UserCreateRequest request) {
        String userId = request.getUserId().toUpperCase();
        if (userRepository.existsById(userId)) {
            throw new BadRequestException("User ID already exists: " + userId);
        }

        User user = new User();
        user.setUserId(userId);
        user.setFirstName(request.getFirstName());
        user.setLastName(request.getLastName());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setUserType(request.getUserType());

        userRepository.save(user);
        return UserDto.fromEntity(user);
    }

    @Transactional
    public UserDto updateUser(String userId, UserUpdateRequest request) {
        User user = userRepository.findById(userId.toUpperCase())
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));

        if (request.getFirstName() != null) {
            user.setFirstName(request.getFirstName());
        }
        if (request.getLastName() != null) {
            user.setLastName(request.getLastName());
        }
        if (request.getPassword() != null) {
            user.setPassword(passwordEncoder.encode(request.getPassword()));
        }
        if (request.getUserType() != null) {
            user.setUserType(request.getUserType());
        }

        userRepository.save(user);
        return UserDto.fromEntity(user);
    }

    @Transactional
    public void deleteUser(String userId) {
        User user = userRepository.findById(userId.toUpperCase())
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));
        userRepository.delete(user);
    }
}
