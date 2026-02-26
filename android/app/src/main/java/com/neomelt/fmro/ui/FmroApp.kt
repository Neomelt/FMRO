package com.neomelt.fmro.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun FmroApp(vm: FmroViewModel = viewModel()) {
    val ui by vm.uiState.collectAsStateWithLifecycle()
    var showAddDialog by remember { mutableStateOf(false) }

    val visibleItems = if (ui.selectedStage == "All") {
        ui.items
    } else {
        ui.items.filter { it.stage == ui.selectedStage }
    }

    Scaffold(
        floatingActionButton = {
            FloatingActionButton(onClick = { showAddDialog = true }) {
                Text("+")
            }
        }
    ) { innerPadding ->
        DashboardScreen(
            innerPadding = innerPadding,
            ui = ui,
            visibleItems = visibleItems,
            onRefresh = vm::refresh,
            onStageSelect = vm::selectStage,
            onSelectItem = vm::selectItem,
            onNextStage = vm::moveToNextStage,
            onReject = vm::markRejected,
            onOffer = vm::markOffer,
        )
    }

    if (showAddDialog) {
        AddApplicationDialog(
            onDismiss = { showAddDialog = false },
            onConfirm = { company, role ->
                vm.addApplication(company, role)
                showAddDialog = false
            }
        )
    }
}

@Composable
private fun DashboardScreen(
    innerPadding: PaddingValues,
    ui: FmroUiState,
    visibleItems: List<UiDashboardItem>,
    onRefresh: () -> Unit,
    onStageSelect: (String) -> Unit,
    onSelectItem: (Long) -> Unit,
    onNextStage: (Long) -> Unit,
    onReject: (Long) -> Unit,
    onOffer: (Long) -> Unit,
) {
    val selectedItem = ui.items.firstOrNull { it.id == ui.selectedId }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Column {
                Text("FMRO", style = MaterialTheme.typography.headlineSmall)
                Text("Find Much Robot Offer", style = MaterialTheme.typography.bodyMedium)
            }
            OutlinedButton(onClick = onRefresh) {
                Text("Refresh")
            }
        }

        if (ui.loading) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                CircularProgressIndicator(modifier = Modifier.padding(top = 2.dp))
                Text("Loading applications...")
            }
        }

        if (ui.syncing) {
            Text("Syncing changes...", style = MaterialTheme.typography.labelMedium)
        }

        ui.error?.let { msg ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Text(msg, modifier = Modifier.padding(10.dp), style = MaterialTheme.typography.bodySmall)
            }
        }

        StatsRow(items = ui.items)
        StageFilters(selectedStage = ui.selectedStage, onStageSelect = onStageSelect)

        LazyColumn(
            modifier = Modifier.weight(1f, fill = true),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            if (visibleItems.isEmpty()) {
                item {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            "No items in this stage yet.",
                            modifier = Modifier.padding(12.dp),
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }
                }
            } else {
                items(visibleItems, key = { it.id }) { item ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelectItem(item.id) }
                    ) {
                        Column(
                            modifier = Modifier.padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp),
                        ) {
                            Text(item.company, style = MaterialTheme.typography.titleSmall)
                            Text(item.role, style = MaterialTheme.typography.bodyMedium)
                            Text("Stage: ${item.stage}", style = MaterialTheme.typography.bodySmall)
                            Text("Deadline: ${item.deadline}", style = MaterialTheme.typography.bodySmall)
                            if (ui.selectedId == item.id) {
                                Text("Selected", style = MaterialTheme.typography.labelSmall)
                            }
                        }
                    }
                }
            }
        }

        if (selectedItem != null) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Quick Actions", style = MaterialTheme.typography.titleSmall)
                    Text("${selectedItem.company} · ${selectedItem.role}")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { onNextStage(selectedItem.id) }) {
                            Text("Next Stage")
                        }
                        OutlinedButton(onClick = { onReject(selectedItem.id) }) {
                            Text("Reject")
                        }
                        Button(onClick = { onOffer(selectedItem.id) }) {
                            Text("Offer")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun AddApplicationDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, String) -> Unit,
) {
    var company by remember { mutableStateOf("") }
    var role by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Application") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = company,
                    onValueChange = { company = it },
                    label = { Text("Company") },
                    singleLine = true,
                )
                OutlinedTextField(
                    value = role,
                    onValueChange = { role = it },
                    label = { Text("Role") },
                    singleLine = true,
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(company, role) },
                enabled = company.isNotBlank() && role.isNotBlank(),
            ) {
                Text("Add")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}

@Composable
private fun StatsRow(items: List<UiDashboardItem>) {
    val offerCount = items.count { it.stage == "Offer" }
    val interviewCount = items.count { it.stage.startsWith("Interview") }
    val pendingCount = items.count { it.stage == "Applied" || it.stage == "OA" }

    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        StatCard("Pending", pendingCount, Modifier.weight(1f))
        StatCard("Interview", interviewCount, Modifier.weight(1f))
        StatCard("Offer", offerCount, Modifier.weight(1f))
    }
}

@Composable
private fun StatCard(label: String, value: Int, modifier: Modifier = Modifier) {
    Card(modifier = modifier) {
        Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(label, style = MaterialTheme.typography.labelMedium)
            Text(value.toString(), style = MaterialTheme.typography.titleLarge)
        }
    }
}

@Composable
private fun StageFilters(selectedStage: String, onStageSelect: (String) -> Unit) {
    val stages = listOf("All") + stageFlow + listOf("Rejected")
    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        items(stages) { stage ->
            val selected = stage == selectedStage
            if (selected) {
                Button(onClick = { onStageSelect(stage) }) {
                    Text(stage)
                }
            } else {
                OutlinedButton(onClick = { onStageSelect(stage) }) {
                    Text(stage)
                }
            }
        }
    }
}
