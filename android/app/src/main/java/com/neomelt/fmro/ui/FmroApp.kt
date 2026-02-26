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
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.runtime.toMutableStateList
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

data class DashboardItem(
    val id: Int,
    val company: String,
    val role: String,
    val stage: String,
    val deadline: String,
)

private val stageFlow = listOf("Applied", "OA", "Interview #1", "Interview #2", "HR", "Offer")

private fun nextStage(stage: String): String {
    val idx = stageFlow.indexOf(stage)
    return if (idx == -1 || idx == stageFlow.lastIndex) stage else stageFlow[idx + 1]
}

@Composable
fun FmroApp() {
    val items = remember {
        listOf(
            DashboardItem(1, "DJI", "Robotics Intern", "Applied", "2026-03-31"),
            DashboardItem(2, "Unitree", "Perception Intern", "Interview #1", "2026-03-05"),
            DashboardItem(3, "AgiBot", "SLAM Intern", "OA", "2026-03-10"),
        ).toMutableStateList()
    }
    var selectedStage by remember { mutableStateOf("All") }
    var selectedId by remember { mutableStateOf<Int?>(1) }
    var nextId by remember { mutableIntStateOf(4) }

    val visibleItems = if (selectedStage == "All") items else items.filter { it.stage == selectedStage }
    val selectedItem = items.firstOrNull { it.id == selectedId }

    Scaffold(
        floatingActionButton = {
            FloatingActionButton(
                onClick = {
                    val fresh = DashboardItem(
                        id = nextId,
                        company = "New Robotics Co.",
                        role = "Control Intern",
                        stage = "Applied",
                        deadline = "2026-04-01",
                    )
                    nextId += 1
                    items.add(0, fresh)
                    selectedId = fresh.id
                }
            ) {
                Text("+")
            }
        }
    ) { innerPadding ->
        DashboardScreen(
            innerPadding = innerPadding,
            items = items,
            visibleItems = visibleItems,
            selectedStage = selectedStage,
            onStageSelect = { selectedStage = it },
            selectedId = selectedId,
            onSelectItem = { selectedId = it },
            selectedItem = selectedItem,
        )
    }
}

@Composable
private fun DashboardScreen(
    innerPadding: PaddingValues,
    items: SnapshotStateList<DashboardItem>,
    visibleItems: List<DashboardItem>,
    selectedStage: String,
    onStageSelect: (String) -> Unit,
    selectedId: Int?,
    onSelectItem: (Int) -> Unit,
    selectedItem: DashboardItem?,
) {
    val updateItem: (Int, (DashboardItem) -> DashboardItem) -> Unit = { id, mapper ->
        val idx = items.indexOfFirst { it.id == id }
        if (idx >= 0) {
            items[idx] = mapper(items[idx])
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("FMRO", style = MaterialTheme.typography.headlineSmall)
        Text("Find Much Robot Offer", style = MaterialTheme.typography.bodyMedium)

        StatsRow(items = items)

        StageFilters(selectedStage = selectedStage, onStageSelect = onStageSelect)

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
                            if (selectedId == item.id) {
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
                        OutlinedButton(onClick = {
                            updateItem(selectedItem.id) { it.copy(stage = nextStage(it.stage)) }
                        }) {
                            Text("Next Stage")
                        }
                        OutlinedButton(onClick = {
                            updateItem(selectedItem.id) { it.copy(stage = "Rejected") }
                        }) {
                            Text("Reject")
                        }
                        Button(onClick = {
                            updateItem(selectedItem.id) { it.copy(stage = "Offer") }
                        }) {
                            Text("Offer")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatsRow(items: List<DashboardItem>) {
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
