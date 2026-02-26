package com.neomelt.fmro.data

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.neomelt.fmro.BuildConfig
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit

object FmroApiClient {
    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
    }

    private val logging = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BASIC
    }

    private val client = OkHttpClient.Builder()
        .addInterceptor(logging)
        .build()

    @Volatile
    private var baseUrl: String = normalizeBaseUrl(BuildConfig.FMRO_API_BASE_URL)

    @Volatile
    private var cachedService: FmroApiService = createService(baseUrl)

    fun service(): FmroApiService = cachedService

    fun currentBaseUrl(): String = baseUrl

    @Synchronized
    fun updateBaseUrl(newBaseUrl: String) {
        val normalized = normalizeBaseUrl(newBaseUrl)
        if (normalized == baseUrl) return
        baseUrl = normalized
        cachedService = createService(baseUrl)
    }

    private fun createService(base: String): FmroApiService {
        return Retrofit.Builder()
            .baseUrl(base)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(FmroApiService::class.java)
    }

    private fun normalizeBaseUrl(raw: String): String {
        val trimmed = raw.trim()
        if (trimmed.isEmpty()) return BuildConfig.FMRO_API_BASE_URL
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }
}
