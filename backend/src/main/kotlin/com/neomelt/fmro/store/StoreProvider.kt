package com.neomelt.fmro.store

import com.neomelt.fmro.db.DatabaseFactory

object StoreProvider {
    val store: FmroStore by lazy {
        val requested = System.getenv("FMRO_STORE")?.trim()?.lowercase()
        if (requested == "postgres") {
            val ok = DatabaseFactory.initFromEnv()
            if (ok) {
                println("[FMRO] store=postgres")
                PostgresStore
            } else {
                println("[FMRO] store fallback to in-memory (missing FMRO_DB_* env)")
                InMemoryStore
            }
        } else {
            println("[FMRO] store=in-memory")
            InMemoryStore
        }
    }
}
