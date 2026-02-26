package com.neomelt.fmro.db

import org.jetbrains.exposed.sql.Database
import org.jetbrains.exposed.sql.SchemaUtils
import org.jetbrains.exposed.sql.transactions.transaction

object DatabaseFactory {
    private var initialized = false

    fun initFromEnv(): Boolean {
        if (initialized) return true

        val url = System.getenv("FMRO_DB_URL") ?: return false
        val user = System.getenv("FMRO_DB_USER") ?: "postgres"
        val password = System.getenv("FMRO_DB_PASSWORD") ?: "postgres"

        Database.connect(
            url = url,
            driver = "org.postgresql.Driver",
            user = user,
            password = password,
        )

        transaction {
            SchemaUtils.create(
                CompaniesTable,
                JobsTable,
                ApplicationsTable,
                InterviewRoundsTable,
                ReviewQueueTable,
            )
        }

        initialized = true
        return true
    }
}
