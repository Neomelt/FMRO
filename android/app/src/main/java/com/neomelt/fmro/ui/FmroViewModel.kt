package com.neomelt.fmro.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.neomelt.fmro.data.ApiApplication
import com.neomelt.fmro.data.ApiCreateApplicationRequest
import com.neomelt.fmro.data.ApiUpdateApplicationRequest
import com.neomelt.fmro.data.FmroApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.net.URL

enum class AppTab { JOBS, PIPELINE, SETTINGS }
enum class ThemeMode { SYSTEM, LIGHT, DARK }
enum class LanguageMode { SYSTEM, ZH, EN }

data class UiDashboardItem(
    val id: Long,
    val company: String,
    val role: String,
    val stage: String,
    val deadline: String,
)

data class UiJobItem(
    val id: Long,
    val company: String,
    val title: String,
    val location: String,
    val deadline: String,
    val applyUrl: String,
    val sourceUrl: String,
)

data class FmroUiState(
    val loading: Boolean = true,
    val syncing: Boolean = false,
    val error: String? = null,
    val selectedTab: AppTab = AppTab.JOBS,
    val selectedStage: String = "All",
    val selectedId: Long? = null,
    val items: List<UiDashboardItem> = emptyList(),
    val jobs: List<UiJobItem> = emptyList(),
    val selectedJobId: Long? = null,
    val jobKeyword: String = "",
    val cityFilter: String = "All",
    val bookmarkedJobIds: Set<Long> = emptySet(),
    val themeMode: ThemeMode = ThemeMode.SYSTEM,
    val languageMode: LanguageMode = LanguageMode.ZH,
    val autoUpdateEnabled: Boolean = true,
    val crawlerImportLimit: Int = 50,
    val updateStatus: String? = null,
    val latestVersion: String? = null,
    val releaseUrl: String? = null,
    val updateApkUrl: String? = null,
    val backendBaseUrl: String = FmroApiClient.currentBaseUrl(),
)

class FmroViewModel : ViewModel() {
    private val api get() = FmroApiClient.service()
    private val _uiState = MutableStateFlow(FmroUiState())
    val uiState: StateFlow<FmroUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(loading = true, error = null) }

            runCatching {
                val companies = api.companies().associateBy { it.id }
                val jobs = api.jobs().map { job ->
                    UiJobItem(
                        id = job.id,
                        company = companies[job.companyId]?.name ?: "Company #${job.companyId}",
                        title = job.title,
                        location = job.location ?: "Unknown",
                        deadline = job.deadlineAt?.take(10) ?: "TBD",
                        applyUrl = job.applyUrl ?: "",
                        sourceUrl = job.sourceUrl ?: "",
                    )
                }
                val apps = api.applications().map { it.toUi() }
                jobs to apps
            }.onSuccess { (jobs, apps) ->
                _uiState.update { state ->
                    state.copy(
                        loading = false,
                        jobs = jobs,
                        items = apps,
                        selectedId = apps.firstOrNull()?.id,
                        selectedJobId = jobs.firstOrNull()?.id,
                        error = null,
                    )
                }
            }.onFailure { err ->
                _uiState.update { state ->
                    state.copy(
                        loading = false,
                        error = "Backend unreachable: ${err.message ?: "unknown"}",
                    )
                }
            }
        }
    }

    fun selectTab(tab: AppTab) {
        _uiState.update { it.copy(selectedTab = tab) }
    }

    fun selectStage(stage: String) {
        _uiState.update { it.copy(selectedStage = stage) }
    }

    fun selectItem(id: Long) {
        _uiState.update { it.copy(selectedId = id) }
    }

    fun selectJob(id: Long?) {
        _uiState.update { it.copy(selectedJobId = id) }
    }

    fun setJobKeyword(keyword: String) {
        _uiState.update { it.copy(jobKeyword = keyword) }
    }

    fun setCityFilter(city: String) {
        _uiState.update { it.copy(cityFilter = city) }
    }

    fun toggleBookmark(jobId: Long) {
        _uiState.update { state ->
            val next = state.bookmarkedJobIds.toMutableSet()
            if (!next.add(jobId)) {
                next.remove(jobId)
            }
            state.copy(bookmarkedJobIds = next)
        }
    }

    fun setThemeMode(mode: ThemeMode) {
        _uiState.update { it.copy(themeMode = mode) }
    }

    fun setLanguageMode(mode: LanguageMode) {
        _uiState.update { it.copy(languageMode = mode) }
    }

    fun setAutoUpdate(enabled: Boolean) {
        _uiState.update { it.copy(autoUpdateEnabled = enabled) }
    }

    fun setBackendBaseUrlInput(url: String) {
        _uiState.update { it.copy(backendBaseUrl = url) }
    }

    fun applyBackendBaseUrl() {
        val url = _uiState.value.backendBaseUrl
        runCatching {
            FmroApiClient.updateBaseUrl(url)
        }.onSuccess {
            _uiState.update {
                it.copy(
                    updateStatus = "Backend set: ${FmroApiClient.currentBaseUrl()}",
                    error = null,
                )
            }
            refresh()
        }.onFailure { err ->
            _uiState.update {
                it.copy(error = "Invalid backend URL: ${err.message ?: "unknown"}")
            }
        }
    }

    fun setCrawlerImportLimit(limit: Int) {
        _uiState.update { it.copy(crawlerImportLimit = limit) }
    }

    fun addApplication(company: String, role: String) {
        if (company.isBlank() || role.isBlank()) return

        val optimisticId = -(System.currentTimeMillis())
        val optimistic = UiDashboardItem(
            id = optimisticId,
            company = company.trim(),
            role = role.trim(),
            stage = "Applied",
            deadline = "TBD",
        )

        _uiState.update {
            it.copy(
                items = listOf(optimistic) + it.items,
                selectedId = optimisticId,
                syncing = true,
                error = null,
            )
        }

        viewModelScope.launch {
            runCatching {
                api.createApplication(
                    ApiCreateApplicationRequest(
                        companyName = company.trim(),
                        role = role.trim(),
                        stage = "Applied",
                    )
                )
            }.onSuccess { created ->
                _uiState.update { state ->
                    state.copy(
                        syncing = false,
                        items = state.items.map { if (it.id == optimisticId) created.toUi() else it },
                        selectedId = created.id,
                    )
                }
            }.onFailure {
                _uiState.update { it.copy(syncing = false, error = "Saved locally only (API failed)") }
            }
        }
    }

    fun addApplicationFromJob(job: UiJobItem) {
        addApplication(company = job.company, role = job.title)
    }

    fun moveToNextStage(id: Long) {
        val current = _uiState.value.items.firstOrNull { it.id == id } ?: return
        val next = nextStage(current.stage)
        updateStage(id, next)
    }

    fun markRejected(id: Long) = updateStage(id, "Rejected")

    fun markOffer(id: Long) = updateStage(id, "Offer")

    fun deleteApplication(id: Long) {
        val previous = _uiState.value.items
        _uiState.update { state ->
            val nextItems = state.items.filterNot { it.id == id }
            state.copy(
                items = nextItems,
                selectedId = nextItems.firstOrNull()?.id,
                syncing = true,
                error = null,
            )
        }

        if (id <= 0) {
            _uiState.update { it.copy(syncing = false) }
            return
        }

        viewModelScope.launch {
            runCatching {
                api.deleteApplication(id)
            }.onSuccess {
                _uiState.update { it.copy(syncing = false) }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        syncing = false,
                        items = previous,
                        selectedId = previous.firstOrNull()?.id,
                        error = "Delete failed (API unreachable)",
                    )
                }
            }
        }
    }

    fun crawlAndImportJobs() {
        viewModelScope.launch {
            val limit = _uiState.value.crawlerImportLimit
            _uiState.update { it.copy(syncing = true, updateStatus = "Crawling careers pages...") }

            runCatching {
                val run = api.runCrawler()
                val pending = api.reviewQueue("pending")
                val imported = pending.take(limit)
                imported.forEach { api.approveReview(it.id) }
                "Crawled ${run.scannedCompanies} companies, imported ${imported.size} entries"
            }.onSuccess { msg ->
                _uiState.update { it.copy(syncing = false, updateStatus = msg) }
                refresh()
            }.onFailure { err ->
                _uiState.update {
                    it.copy(syncing = false, updateStatus = "Crawl failed: ${err.message ?: "unknown"}")
                }
            }
        }
    }

    fun checkUpdates() {
        viewModelScope.launch {
            _uiState.update { it.copy(syncing = true, updateStatus = "Checking release updates...") }

            runCatching {
                withContext(Dispatchers.IO) {
                    val text = URL("https://api.github.com/repos/Neomelt/FMRO/releases/latest").readText()
                    val obj = Json.parseToJsonElement(text).jsonObject
                    val tag = obj["tag_name"]?.jsonPrimitive?.content ?: "unknown"
                    val releasePage = obj["html_url"]?.jsonPrimitive?.content ?: ""
                    val apkUrl = obj["assets"]
                        ?.jsonArray
                        ?.firstOrNull { asset ->
                            val name = asset.jsonObject["name"]?.jsonPrimitive?.content.orEmpty()
                            name.endsWith("-debug.apk") || name.endsWith(".apk")
                        }
                        ?.jsonObject
                        ?.get("browser_download_url")
                        ?.jsonPrimitive
                        ?.content
                        ?: ""
                    Triple(tag, releasePage, apkUrl)
                }
            }.onSuccess { (tag, releasePage, apkUrl) ->
                _uiState.update {
                    it.copy(
                        syncing = false,
                        latestVersion = tag,
                        releaseUrl = releasePage,
                        updateApkUrl = apkUrl.ifBlank { null },
                        updateStatus = if (apkUrl.isBlank()) {
                            "Latest release: $tag"
                        } else {
                            "Latest release: $tag (ready to update)"
                        },
                    )
                }
            }.onFailure {
                _uiState.update { it.copy(syncing = false, updateStatus = "Update check failed") }
            }
        }
    }

    private fun updateStage(id: Long, stage: String) {
        _uiState.update { state ->
            state.copy(
                items = state.items.map { if (it.id == id) it.copy(stage = stage) else it },
                syncing = true,
                error = null,
            )
        }

        if (id <= 0) {
            _uiState.update { it.copy(syncing = false) }
            return
        }

        viewModelScope.launch {
            runCatching {
                api.updateApplication(id, ApiUpdateApplicationRequest(stage = stage))
            }.onSuccess {
                _uiState.update { it.copy(syncing = false) }
            }.onFailure {
                _uiState.update { it.copy(syncing = false, error = "Stage updated locally (API failed)") }
            }
        }
    }

    private fun ApiApplication.toUi(): UiDashboardItem = UiDashboardItem(
        id = id,
        company = companyName,
        role = role,
        stage = stage,
        deadline = deadlineAt?.take(10) ?: "TBD",
    )

}

val stageFlow = listOf("Applied", "OA", "Interview #1", "Interview #2", "HR", "Offer")

fun nextStage(stage: String): String {
    val idx = stageFlow.indexOf(stage)
    return if (idx == -1 || idx == stageFlow.lastIndex) stage else stageFlow[idx + 1]
}
