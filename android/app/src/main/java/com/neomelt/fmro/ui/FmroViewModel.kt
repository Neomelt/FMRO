package com.neomelt.fmro.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.neomelt.fmro.data.ApiApplication
import com.neomelt.fmro.data.ApiCreateApplicationRequest
import com.neomelt.fmro.data.ApiUpdateApplicationRequest
import com.neomelt.fmro.data.FmroApiClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class UiDashboardItem(
    val id: Long,
    val company: String,
    val role: String,
    val stage: String,
    val deadline: String,
)

data class FmroUiState(
    val loading: Boolean = true,
    val syncing: Boolean = false,
    val error: String? = null,
    val selectedStage: String = "All",
    val selectedId: Long? = null,
    val items: List<UiDashboardItem> = emptyList(),
)

class FmroViewModel : ViewModel() {
    private val api = FmroApiClient.service
    private val _uiState = MutableStateFlow(FmroUiState())
    val uiState: StateFlow<FmroUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(loading = true, error = null) }
            runCatching { api.applications() }
                .onSuccess { apps ->
                    val mapped = apps.map { it.toUi() }
                    _uiState.update {
                        it.copy(
                            loading = false,
                            items = mapped,
                            selectedId = mapped.firstOrNull()?.id,
                            error = null,
                        )
                    }
                }
                .onFailure { err ->
                    val fallback = fallbackItems()
                    _uiState.update {
                        it.copy(
                            loading = false,
                            items = fallback,
                            selectedId = fallback.firstOrNull()?.id,
                            error = "Using demo data (backend unreachable)",
                        )
                    }
                }
        }
    }

    fun selectStage(stage: String) {
        _uiState.update { it.copy(selectedStage = stage) }
    }

    fun selectItem(id: Long) {
        _uiState.update { it.copy(selectedId = id) }
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

    fun moveToNextStage(id: Long) {
        val current = _uiState.value.items.firstOrNull { it.id == id } ?: return
        val next = nextStage(current.stage)
        updateStage(id, next)
    }

    fun markRejected(id: Long) = updateStage(id, "Rejected")

    fun markOffer(id: Long) = updateStage(id, "Offer")

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

    private fun fallbackItems(): List<UiDashboardItem> = listOf(
        UiDashboardItem(1, "DJI", "Robotics Intern", "Applied", "2026-03-31"),
        UiDashboardItem(2, "Unitree", "Perception Intern", "Interview #1", "2026-03-05"),
        UiDashboardItem(3, "AgiBot", "SLAM Intern", "OA", "2026-03-10"),
    )
}

val stageFlow = listOf("Applied", "OA", "Interview #1", "Interview #2", "HR", "Offer")

fun nextStage(stage: String): String {
    val idx = stageFlow.indexOf(stage)
    return if (idx == -1 || idx == stageFlow.lastIndex) stage else stageFlow[idx + 1]
}
