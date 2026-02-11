package com.carddemo.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.tags.Tag;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI cardDemoOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("CardDemo API")
                        .description("Migrated CardDemo mainframe CICS application - REST API. " +
                                "This API is an exact replica of the IBM mainframe CardDemo credit card management system, " +
                                "migrated from COBOL/CICS to Spring Boot.")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("CardDemo Migration")
                                .url("https://github.com/itsupportTD/MainframeConversion")))
                .components(new Components()
                        .addSecuritySchemes("bearerAuth", new SecurityScheme()
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("JWT token obtained from POST /api/auth/login")))
                .addSecurityItem(new SecurityRequirement().addList("bearerAuth"))
                .tags(List.of(
                        new Tag().name("Authentication").description("Sign-on / Sign-off (COSGN00C equivalent)"),
                        new Tag().name("Accounts").description("Account view and update (COACTVWC, COACTUPC equivalent)"),
                        new Tag().name("Cards").description("Credit card list, search, and update (COCRDLIC, COCRDSLC, COCRDUPC equivalent)"),
                        new Tag().name("Transactions").description("Transaction list, view, and add (COTRN00C, COTRN01C, COTRN02C equivalent)"),
                        new Tag().name("Bill Payment").description("Bill payment - pay balance in full (COBIL00C equivalent)"),
                        new Tag().name("Reports").description("Transaction report submission (CORPT00C equivalent)"),
                        new Tag().name("Admin - Users").description("User CRUD - Admin only (COUSR00C-03C equivalent)"),
                        new Tag().name("Admin - Transaction Types").description("Transaction type management - Admin only (COTRTLIC, COTRTUPC equivalent)")
                ));
    }
}
