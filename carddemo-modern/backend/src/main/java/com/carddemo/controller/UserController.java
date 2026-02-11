package com.carddemo.controller;

import com.carddemo.dto.ApiResponse;
import com.carddemo.dto.UserCreateRequest;
import com.carddemo.dto.UserDto;
import com.carddemo.dto.UserUpdateRequest;
import com.carddemo.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/admin/users")
@PreAuthorize("hasRole('ADMIN')")
@Tag(name = "Admin - Users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping
    @Operation(summary = "List all users (paginated)",
            description = "List all users in the security file. Admin only. " +
                    "Equivalent to COUSR00C (Transaction CU00). " +
                    "Reads from USRSEC file.")
    public ResponseEntity<Page<UserDto>> listUsers(
            @Parameter(description = "Page number (0-based)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(userService.listUsers(PageRequest.of(page, size)));
    }

    @GetMapping("/{userId}")
    @Operation(summary = "Get user details",
            description = "Retrieve a specific user's information. Admin only.")
    public ResponseEntity<UserDto> getUser(@PathVariable String userId) {
        return ResponseEntity.ok(userService.getUser(userId));
    }

    @PostMapping
    @Operation(summary = "Add new user",
            description = "Create a new user account. Admin only. " +
                    "Equivalent to COUSR01C (Transaction CU01). " +
                    "Writes to USRSEC file. Password is hashed with BCrypt (mainframe stored plain text).")
    public ResponseEntity<UserDto> createUser(@Valid @RequestBody UserCreateRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(userService.createUser(request));
    }

    @PutMapping("/{userId}")
    @Operation(summary = "Update existing user",
            description = "Update an existing user's information. Admin only. " +
                    "Equivalent to COUSR02C (Transaction CU02). " +
                    "Updates USRSEC file.")
    public ResponseEntity<UserDto> updateUser(
            @PathVariable String userId, @Valid @RequestBody UserUpdateRequest request) {
        return ResponseEntity.ok(userService.updateUser(userId, request));
    }

    @DeleteMapping("/{userId}")
    @Operation(summary = "Delete user",
            description = "Delete a user account. Admin only. " +
                    "Equivalent to COUSR03C (Transaction CU03). " +
                    "Deletes from USRSEC file.")
    public ResponseEntity<ApiResponse> deleteUser(@PathVariable String userId) {
        userService.deleteUser(userId);
        return ResponseEntity.ok(ApiResponse.success("User deleted successfully: " + userId));
    }
}
