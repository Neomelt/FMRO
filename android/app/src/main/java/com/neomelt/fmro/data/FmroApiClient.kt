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

    val service: FmroApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BuildConfig.FMRO_API_BASE_URL)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(FmroApiService::class.java)
    }
}
