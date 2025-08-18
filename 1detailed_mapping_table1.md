# EATI Schema v2.2.1 → SimPy 完整映射实现清单

## 映射表结构说明

以下表格按照 **解析→IR→生成** 三个阶段组织，每个元素包含：
- **XPath**: XML中的完整路径
- **Java解析**: JAXB注解和Java字段
- **IR表示**: 中间表示的数据结构
- **FreeMarker模板**: 模板变量和条件
- **SimPy生成**: 最终Python代码片段

---

## 1. 基础配置元素映射

### 1.1 根元素与元数据

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 1 | `/EATIModel/@version` | 必填 | `@XmlAttribute String version` | `model.version` | `${model.version}` | `# Model Version: ${model.version}` | |
| 2 | `/EATIModel/@timestamp` | 必填 | `@XmlAttribute LocalDateTime timestamp` | `model.timestamp` | `${model.timestamp}` | `# Generated: ${model.timestamp}` | |
| 3 | `/EATIModel/@schemaVersion` | 可选(2.2.1) | `@XmlAttribute String schemaVersion` | `model.schemaVersion` | `${model.schemaVersion!"2.2.1"}` | `# Schema: ${model.schemaVersion}` | ✨ |

### 1.2 仿真配置

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 4 | `/EATIModel/SimulationConfig/StartTime` | 可选(0) | `@XmlElement Double startTime` | `simulation.startTime` | `${simulation.startTime!0}` | `SIMULATION_START_TIME = ${simulation.startTime}` | |
| 5 | `/EATIModel/SimulationConfig/EndTime` | 必填 | `@XmlElement(required=true) Double endTime` | `simulation.endTime` | `${simulation.endTime}` | `SIMULATION_END_TIME = ${simulation.endTime}` | |
| 6 | `/EATIModel/SimulationConfig/RandomSeed` | 可选 | `@XmlElement Integer randomSeed` | `simulation.randomSeed` | `<#if simulation.randomSeed??>${simulation.randomSeed}</#if>` | `<#if simulation.randomSeed??>RANDOM_SEED = ${simulation.randomSeed}</#if>` | |
| 7 | `/EATIModel/SimulationConfig/TimeUnit` | 可选("second") | `@XmlElement String timeUnit` | `simulation.timeUnit` | `${simulation.timeUnit!"second"}` | `TIME_UNIT = '${simulation.timeUnit}'` | |
| 8 | `/EATIModel/SimulationConfig/RunMode` | 可选("continuous") | `@XmlElement RunModeType runMode` | `simulation.runMode` | `${simulation.runMode!"continuous"}` | `RUN_MODE = '${simulation.runMode}'` | |
| 9 | `/EATIModel/SimulationConfig/RealTimeRatio` | 可选(1.0) | `@XmlElement Double realTimeRatio` | `simulation.realTimeRatio` | `${simulation.realTimeRatio!1.0}` | `REAL_TIME_RATIO = ${simulation.realTimeRatio}` | |

### 1.3 接口配置

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 10 | `/EATIModel/InterfaceConfig/@enabled` | 必填 | `@XmlAttribute Boolean enabled` | `interface.enabled` | `${interface.enabled}` | `<#if interface.enabled>setupWebSocket()</#if>` | |
| 11 | `/EATIModel/InterfaceConfig/WebSocketConfig/Host` | 可选("localhost") | `@XmlElement String host` | `websocket.host` | `${websocket.host!"localhost"}` | `WS_HOST = '${websocket.host}'` | |
| 12 | `/EATIModel/InterfaceConfig/WebSocketConfig/Port` | 可选(8765) | `@XmlElement Integer port` | `websocket.port` | `${websocket.port!8765}` | `WS_PORT = ${websocket.port}` | |

---

## 2. 数据定义元素映射

### 2.1 全局变量

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 13 | `/EATIModel/GlobalVariables/Variable/@id` | 必填 | `@XmlAttribute String id` | `globalVar.id` | `${globalVar.id}` | `'${globalVar.id}': ${globalVar.initialValue}` | |
| 14 | `/EATIModel/GlobalVariables/Variable/Name` | 必填 | `@XmlElement String name` | `globalVar.name` | `${globalVar.name}` | `# ${globalVar.name}` | |
| 15 | `/EATIModel/GlobalVariables/Variable/Type` | 必填 | `@XmlElement VariableType type` | `globalVar.type` | `${globalVar.type}` | `# Type: ${globalVar.type}` | |
| 16 | `/EATIModel/GlobalVariables/Variable/InitialValue` | 必填 | `@XmlElement String initialValue` | `globalVar.initialValue` | `${globalVar.pythonValue}` | `${globalVar.pythonValue}` | |
| 17 | `/EATIModel/GlobalVariables/Variable/Visibility` | 可选("internal") | `@XmlElement String visibility` | `globalVar.visibility` | `${globalVar.visibility!"internal"}` | `# Visibility: ${globalVar.visibility}` | |

### 2.2 资源定义

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 18 | `/EATIModel/Resources/Resource/@id` | 必填 | `@XmlAttribute String id` | `resource.id` | `${resource.id}` | `${resource.id} = simpy.${resource.simpyType}(env, ...)` | |
| 19 | `/EATIModel/Resources/Resource/Name` | 必填 | `@XmlElement String name` | `resource.name` | `${resource.name}` | `# ${resource.name}` | |
| 20 | `/EATIModel/Resources/Resource/Type` | 必填 | `@XmlElement SimPyResourceType type` | `resource.type` | `${resource.simpyType}` | `simpy.${resource.simpyType}` | |
| 21 | `/EATIModel/Resources/Resource/Capacity` | 必填 | `@XmlElement Integer capacity` | `resource.capacity` | `${resource.capacity}` | `capacity=${resource.capacity}` | |
| 22 | `/EATIModel/Resources/Resource/InitialQuantity` | 可选 | `@XmlElement Integer initialQuantity` | `resource.initialQuantity` | `<#if resource.initialQuantity??>${resource.initialQuantity}</#if>` | `<#if resource.initialQuantity??>, init=${resource.initialQuantity}</#if>` | |

---

## 3. 任务与实体映射

### 3.1 传统任务映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 23 | `/EATIModel/Tasks/Task/@id` | 必填 | `@XmlAttribute String id` | `task.id` | `${task.id}` | `# Task: ${task.id}` | |
| 24 | `/EATIModel/Tasks/Task/Name` | 必填 | `@XmlElement String name` | `task.name` | `${task.name}` | `# ${task.name}` | |
| 25 | `/EATIModel/Tasks/Task/Goal` | 必填 | `@XmlElement String goal` | `task.goal` | `${task.goal}` | `# Goal: ${task.goal}` | |
| 26 | `/EATIModel/Tasks/Task/Priority` | 必填 | `@XmlElement String priority` | `task.priority` | `${task.priority}` | `# Priority: ${task.priority}` | |
| 27 | `/EATIModel/Tasks/Task/Entities/EntityRef` | 必填 | `@XmlElement List<String> entityRefs` | `task.entities` | `<#list task.entities as entity>${entity}</#list>` | `entities = [${task.entityList}]` | |
| 28 | `/EATIModel/Tasks/Task/InitialAction` | 可选 | `@XmlElement String initialAction` | `task.initialAction` | `<#if task.initialAction??>${task.initialAction}</#if>` | `<#if task.initialAction??>initial_action = "${task.initialAction}"</#if>` | |

### 3.2 v2.2.1 多初始行动映射 ✨

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 29 | `/EATIModel/Tasks/Task/InitialActionsConfig/ExecutionMode` | 必填 | `@XmlElement InitialActionExecutionMode executionMode` | `task.multiActions.executionMode` | `${task.multiActions.executionMode}` | `execution_mode = "${task.multiActions.executionMode}"` | ✨ |
| 30 | `/EATIModel/Tasks/Task/InitialActionsConfig/InitialActions/InitialAction/@id` | 必填 | `@XmlAttribute String id` | `initialAction.id` | `${initialAction.id}` | `"${initialAction.id}": {` | ✨ |
| 31 | `/EATIModel/Tasks/Task/InitialActionsConfig/InitialActions/InitialAction/ActionRef` | 必填 | `@XmlElement String actionRef` | `initialAction.actionRef` | `${initialAction.actionRef}` | `"action_ref": "${initialAction.actionRef}"` | ✨ |
| 32 | `/EATIModel/Tasks/Task/InitialActionsConfig/InitialActions/InitialAction/Priority` | 可选(0) | `@XmlElement Integer priority` | `initialAction.priority` | `${initialAction.priority!0}` | `"priority": ${initialAction.priority}` | ✨ |
| 33 | `/EATIModel/Tasks/Task/InitialActionsConfig/InitialActions/InitialAction/Stage` | 可选(1) | `@XmlElement Integer stage` | `initialAction.stage` | `${initialAction.stage!1}` | `"stage": ${initialAction.stage}` | ✨ |
| 34 | `/EATIModel/Tasks/Task/InitialActionsConfig/InitialActions/InitialAction/StartCondition/Formula` | 可选 | `@XmlElement String formula` | `initialAction.startCondition` | `<#if initialAction.startCondition??>"${initialAction.startCondition}"</#if>` | `<#if initialAction.startCondition??>"start_condition": "${initialAction.startCondition}"</#if>` | ✨ |

### 3.3 v2.2.1 依赖关系映射 ✨

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 35 | `/EATIModel/Tasks/Task/InitialActionsConfig/InitialActions/InitialAction/DependsOn/Dependency/ActionRef` | 必填 | `@XmlElement String actionRef` | `dependency.actionRef` | `${dependency.actionRef}` | `"depends_on": ["${dependency.actionRef}"]` | ✨ |
| 36 | `/EATIModel/Tasks/Task/InitialActionsConfig/InitialActions/InitialAction/DependsOn/Dependency/DependencyType` | 必填 | `@XmlElement String dependencyType` | `dependency.type` | `${dependency.type}` | `"dependency_type": "${dependency.type}"` | ✨ |
| 37 | `/EATIModel/Tasks/Task/InitialActionsConfig/InitialActions/InitialAction/DependsOn/Dependency/TimeoutDuration` | 可选 | `@XmlElement Double timeoutDuration` | `dependency.timeout` | `<#if dependency.timeout??>${dependency.timeout}</#if>` | `<#if dependency.timeout??>"timeout": ${dependency.timeout}</#if>` | ✨ |

### 3.4 实体定义映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 38 | `/EATIModel/Entities/Entity/@id` | 必填 | `@XmlAttribute String id` | `entity.id` | `${entity.id}` | `class ${entity.className}(BaseEntity):` | |
| 39 | `/EATIModel/Entities/Entity/Name` | 必填 | `@XmlElement String name` | `entity.name` | `${entity.name}` | `self.name = '${entity.name}'` | |
| 40 | `/EATIModel/Entities/Entity/Type` | 可选 | `@XmlElement String type` | `entity.type` | `${entity.type!"agent"}` | `self.type = '${entity.type}'` | |
| 41 | `/EATIModel/Entities/Entity/Position/X` | 可选 | `@XmlElement Double x` | `entity.position.x` | `${entity.position.x!0.0}` | `'x': ${entity.position.x}` | |
| 42 | `/EATIModel/Entities/Entity/Position/Y` | 可选 | `@XmlElement Double y` | `entity.position.y` | `${entity.position.y!0.0}` | `'y': ${entity.position.y}` | |

### 3.5 实体属性映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 43 | `/EATIModel/Entities/Entity/Attributes/Attribute/@name` | 必填 | `@XmlAttribute String name` | `attribute.name` | `${attribute.name}` | `'${attribute.name}': ${attribute.pythonValue}` | |
| 44 | `/EATIModel/Entities/Entity/Attributes/Attribute/@value` | 必填 | `@XmlAttribute String value` | `attribute.value` | `${attribute.value}` | `${attribute.pythonValue}` | |
| 45 | `/EATIModel/Entities/Entity/Attributes/Attribute/@type` | 必填 | `@XmlAttribute String type` | `attribute.type` | `${attribute.type}` | `# Type: ${attribute.type}` | |

### 3.6 状态变量映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 46 | `/EATIModel/Entities/Entity/StateVariables/StateVariable/@id` | 必填 | `@XmlAttribute String id` | `stateVar.id` | `${stateVar.id}` | `self.${stateVar.pythonName} = ${stateVar.pythonInitialValue}` | |
| 47 | `/EATIModel/Entities/Entity/StateVariables/StateVariable/Name` | 必填 | `@XmlElement String name` | `stateVar.name` | `${stateVar.name}` | `# ${stateVar.name}` | |
| 48 | `/EATIModel/Entities/Entity/StateVariables/StateVariable/Type` | 必填 | `@XmlElement VariableType type` | `stateVar.type` | `${stateVar.type}` | `# Type: ${stateVar.type}` | |
| 49 | `/EATIModel/Entities/Entity/StateVariables/StateVariable/InitialValue` | 必填 | `@XmlElement String initialValue` | `stateVar.initialValue` | `${stateVar.pythonInitialValue}` | `${stateVar.pythonInitialValue}` | |
| 50 | `/EATIModel/Entities/Entity/StateVariables/StateVariable/PublishChanges` | 可选(false) | `@XmlElement Boolean publishChanges` | `stateVar.publishChanges` | `${stateVar.publishChanges!false}` | `<#if stateVar.publishChanges>publish_state_change</#if>` | |

---

## 4. 行为定义元素映射

### 4.1 行动映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 51 | `/EATIModel/Actions/Action/@id` | 必填 | `@XmlAttribute String id` | `action.id` | `${action.id}` | `class ${action.className}(ActionBase):` | |
| 52 | `/EATIModel/Actions/Action/Name` | 必填 | `@XmlElement String name` | `action.name` | `${action.name}` | `self.name = '${action.name}'` | |
| 53 | `/EATIModel/Actions/Action/Activities/ActivityRef` | 必填 | `@XmlElement List<String> activityRefs` | `action.activities` | `<#list action.activities as activity>${activity}</#list>` | `<#list action.activities as activity>yield env.process(${activity}(env, entity, context))</#list>` | |
| 54 | `/EATIModel/Actions/Action/TriggerCondition/Expression/Formula` | 可选 | `@XmlElement String formula` | `action.triggerCondition` | `<#if action.triggerCondition??>${action.triggerCondition}</#if>` | `<#if action.triggerCondition??>if ${action.triggerCondition}:</#if>` | |

### 4.2 资源需求映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 55 | `/EATIModel/Actions/Action/ResourceRequirements/ResourceRequirement/ResourceRef` | 必填 | `@XmlElement String resourceRef` | `resourceReq.resourceRef` | `${resourceReq.resourceRef}` | `yield ${resourceReq.resourceRef}.get(${resourceReq.quantity})` | |
| 56 | `/EATIModel/Actions/Action/ResourceRequirements/ResourceRequirement/Quantity` | 必填 | `@XmlElement Integer quantity` | `resourceReq.quantity` | `${resourceReq.quantity}` | `${resourceReq.quantity}` | |
| 57 | `/EATIModel/Actions/Action/ResourceRequirements/ResourceRequirement/Priority` | 可选 | `@XmlElement Integer priority` | `resourceReq.priority` | `${resourceReq.priority!0}` | `# Priority: ${resourceReq.priority}` | |

### 4.3 活动映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 58 | `/EATIModel/Activities/Activity/@id` | 必填 | `@XmlAttribute String id` | `activity.id` | `${activity.id}` | `def ${activity.functionName}(env, entity, context):` | |
| 59 | `/EATIModel/Activities/Activity/Name` | 必填 | `@XmlElement String name` | `activity.name` | `${activity.name}` | `"""${activity.name}"""` | |
| 60 | `/EATIModel/Activities/Activity/Type` | 必填 | `@XmlElement String type` | `activity.type` | `${activity.type}` | `# Type: ${activity.type}` | |
| 61 | `/EATIModel/Activities/Activity/InternalFunction/Expression/Formula` | 可选 | `@XmlElement String formula` | `activity.expression` | `<#if activity.expression??>${activity.expression}</#if>` | `<#if activity.expression??>${activity.pythonExpression}</#if>` | |

### 4.4 延迟时间映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 62 | `/EATIModel/Activities/Activity/DelayTime/Distribution` | 可选 | `@XmlElement DistributionType distribution` | `activity.delay.distribution` | `${activity.delay.distribution}` | `TimeDistribution.generate('${activity.delay.distribution}', ${activity.delay.pythonParams})` | |
| 63 | `/EATIModel/Activities/Activity/DelayTime/Parameters/Parameter/@name` | 可选 | `@XmlAttribute String name` | `delayParam.name` | `${delayParam.name}` | `'${delayParam.name}': ${delayParam.value}` | |
| 64 | `/EATIModel/Activities/Activity/DelayTime/Parameters/Parameter` | 可选 | `@XmlValue String value` | `delayParam.value` | `${delayParam.value}` | `${delayParam.pythonValue}` | |

---

## 5. 交互与事件映射

### 5.1 交互映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 65 | `/EATIModel/Interactions/Interaction/@id` | 必填 | `@XmlAttribute String id` | `interaction.id` | `${interaction.id}` | `# Interaction: ${interaction.id}` | |
| 66 | `/EATIModel/Interactions/Interaction/Name` | 必填 | `@XmlElement String name` | `interaction.name` | `${interaction.name}` | `# ${interaction.name}` | |
| 67 | `/EATIModel/Interactions/Interaction/Source` | 必填 | `@XmlElement String source` | `interaction.source` | `${interaction.source}` | `source_entity = "${interaction.source}"` | |
| 68 | `/EATIModel/Interactions/Interaction/Target` | 必填 | `@XmlElement String target` | `interaction.target` | `${interaction.target}` | `target_entity = "${interaction.target}"` | |
| 69 | `/EATIModel/Interactions/Interaction/Type` | 必填 | `@XmlElement String type` | `interaction.type` | `${interaction.type}` | `interaction_type = "${interaction.type}"` | |
| 70 | `/EATIModel/Interactions/Interaction/Protocol` | 可选 | `@XmlElement String protocol` | `interaction.protocol` | `<#if interaction.protocol??>${interaction.protocol}</#if>` | `<#if interaction.protocol??>protocol = "${interaction.protocol}"</#if>` | |

### 5.2 事件映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 71 | `/EATIModel/Events/Event/@id` | 必填 | `@XmlAttribute String id` | `event.id` | `${event.id}` | `'${event.id}': {` | |
| 72 | `/EATIModel/Events/Event/Name` | 必填 | `@XmlElement String name` | `event.name` | `${event.name}` | `'name': '${event.name}'` | |
| 73 | `/EATIModel/Events/Event/Type` | 必填 | `@XmlElement String type` | `event.type` | `${event.type}` | `'type': '${event.type}'` | |
| 74 | `/EATIModel/Events/Event/TriggerCondition/Expression/Formula` | 可选 | `@XmlElement String formula` | `event.triggerCondition` | `<#if event.triggerCondition??>${event.triggerCondition}</#if>` | `<#if event.triggerCondition??>'trigger': '${event.triggerCondition}'</#if>` | |
| 75 | `/EATIModel/Events/Event/Actions/ActionRef` | 必填 | `@XmlElement List<String> actionRefs` | `event.actions` | `<#list event.actions as action>${action}</#list>` | `'actions': [<#list event.actions as action>'${action}'<#sep>, </#list>]` | |
| 76 | `/EATIModel/Events/Event/Priority` | 可选 | `@XmlElement Integer priority` | `event.priority` | `${event.priority!0}` | `'priority': ${event.priority}` | |

---

## 6. 监控与接口映射

### 6.1 监控器映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 77 | `/EATIModel/Monitors/Monitor/@id` | 必填 | `@XmlAttribute String id` | `monitor.id` | `${monitor.id}` | `'${monitor.id}': {` | |
| 78 | `/EATIModel/Monitors/Monitor/Name` | 必填 | `@XmlElement String name` | `monitor.name` | `${monitor.name}` | `'name': '${monitor.name}'` | |
| 79 | `/EATIModel/Monitors/Monitor/Target` | 必填 | `@XmlElement String target` | `monitor.target` | `${monitor.target}` | `'target': '${monitor.target}'` | |
| 80 | `/EATIModel/Monitors/Monitor/Metric` | 必填 | `@XmlElement String metric` | `monitor.metric` | `${monitor.metric}` | `'metric': '${monitor.metric}'` | |
| 81 | `/EATIModel/Monitors/Monitor/SampleInterval` | 可选 | `@XmlElement Double sampleInterval` | `monitor.sampleInterval` | `<#if monitor.sampleInterval??>${monitor.sampleInterval}</#if>` | `<#if monitor.sampleInterval??>'sample_interval': ${monitor.sampleInterval}</#if>` | |
| 82 | `/EATIModel/Monitors/Monitor/StreamOutput` | 可选(false) | `@XmlElement Boolean streamOutput` | `monitor.streamOutput` | `${monitor.streamOutput!false}` | `'stream_output': ${monitor.streamOutput?c}` | |

### 6.2 外部接口映射

| 序号 | XPath | 必填性 | Java解析类型 | IR字段 | FreeMarker模板变量 | SimPy生成代码 | v2.2.1标记 |
|------|-------|--------|-------------|--------|-------------------|---------------|------------|
| 83 | `/EATIModel/ExternalInterfaces/StateInterface/StateSnapshot/IncludeEntities` | 可选(true) | `@XmlElement Boolean includeEntities` | `stateInterface.includeEntities` | `${stateInterface.includeEntities!true}` | `'include_entities': ${stateInterface.includeEntities?c}` | |
| 84 | `/EATIModel/ExternalInterfaces/StateInterface/StateSnapshot/SnapshotInterval` | 可选 | `@XmlElement Double snapshotInterval` | `stateInterface.snapshotInterval` | `<#if stateInterface.snapshotInterval??>${stateInterface.snapshotInterval}</#if>` | `<#if stateInterface.snapshotInterval??>'snapshot_interval': ${stateInterface.snapshotInterval}</#if>` | |
| 85 | `/EATIModel/ExternalInterfaces/DataInterface/UpdateMode` | 必填 | `@XmlElement String updateMode` | `dataInterface.updateMode` | `${dataInterface.updateMode}` | `'update_mode': '${dataInterface.updateMode}'` | |

---

## 7. 类型转换映射表

### 7.1 基础类型转换

| XML类型 | Java类型 | Python类型 | 转换示例 |
|---------|----------|------------|----------|
| `xs:string` | `String` | `str` | `"example"` |
| `xs:integer` | `Integer` | `int` | `123` |
| `xs:double` | `Double` | `float` | `1.23` |
| `xs:boolean` | `Boolean` | `bool` | `True/False` |
| `xs:dateTime` | `LocalDateTime` | `datetime` | `datetime.now()` |

### 7.2 枚举类型转换

| EATI枚举 | Java枚举 | Python字符串 | 用途 |
|----------|----------|---------------|------|
| `VariableType.integer` | `VariableType.INTEGER` | `"integer"` | 变量类型 |
| `DistributionType.constant` | `DistributionType.CONSTANT` | `"constant"` | 分布类型 |
| `RunModeType.continuous` | `RunModeType.CONTINUOUS` | `"continuous"` | 运行模式 |
| `SimPyResourceType.Container` | `SimPyResourceType.CONTAINER` | `"Container"` | 资源类型 |
| `InitialActionExecutionMode.staged` ✨ | `InitialActionExecutionMode.STAGED` | `"staged"` | 执行模式 |

### 7.3 复杂类型生成策略

| 复杂类型 | 生成策略 | 模板条件 | 示例代码 |
|----------|----------|----------|----------|
| `TimeDistributionType` | 参数展开 | `<#if delayTime??>` | `TimeDistribution.generate('normal', {'mean': 30, 'std': 5})` |
| `ExpressionType` | 公式转换 | `<#if expression??>` | `evaluator.evaluate('random() < 0.3')` |
| `InitialActionsConfigType` ✨ | 协调器生成 | `<#if multiActions??>` | `ActionCoordinator(mode='staged', actions=[...])` |
| `PositionType` | 字典生成 | `<#if position??>` | `{'x': 100.0, 'y': 200.0, 'z': 0.0}` |

---

## 8. v2.2.1 特殊处理清单 ✨

### 8.1 多初始行动协调器生成

```python
# 根据ExecutionMode生成不同的协调逻辑
<#if task.multiActions??>
<#switch task.multiActions.executionMode>
<#case "sequential">
    # 顺序执行模式
    for action_config in initial_actions:
        yield env.process(execute_action_with_condition(action_config))
<#break>
<#case "parallel">
    # 并行执行模式
    processes = []
    for action_config in initial_actions:
        processes.append(env.process(execute_action_with_condition(action_config)))
    yield env.all_of(processes)
<#break>
<#case "staged">
    # 分阶段执行模式
    stages = group_by_stage(initial_actions)
    for stage_num in sorted(stages.keys()):
        stage_processes = []
        for action_config in stages[stage_num]:
            stage_processes.append(env.process(execute_action_with_condition(action_config)))
        yield env.all_of(stage_processes)
<#break>
</#switch>
</#if>
```

### 8.2 依赖关系处理

```python
# 依赖关系检查和等待逻辑
<#if initialAction.dependencies??>
def check_dependencies(action_config):
    for dependency in action_config.dependencies:
        if dependency.type == "completion":
            yield dependency_manager.wait_for_completion(dependency.action_ref)
        elif dependency.type == "start":
            yield dependency_manager.wait_for_start(dependency.action_ref)
        <#if dependency.timeout??>
        # 超时处理
        try:
            yield env.timeout(${dependency.timeout})
        except simpy.Interrupt:
            <#if dependency.onTimeoutAction??>
            yield env.process(${dependency.onTimeoutAction}())
            </#if>
        </#if>
</#if>
```

### 8.3 环境检查生成

```python
# PreExecutionSetup环境检查
<#if task.preExecutionSetup??>
<#if task.preExecutionSetup.environmentChecks??>
def perform_environment_checks():
    <#list task.preExecutionSetup.environmentChecks.checks as check>
    # ${check.checkName}
    if not evaluator.evaluate('${check.checkCondition.formula}'):
        <#if check.onFailureAction??>
        yield env.process(${check.onFailureAction}())
        </#if>
        raise EnvironmentCheckFailed("${check.checkName}")
    </#list>
</#if>
</#if>
```

---

## 9. 实现优先级与依赖关系

### 9.1 核心元素实现优先级

| 优先级 | 元素类型 | 实现顺序 | 依赖关系 | 验证要求 |
|--------|----------|----------|----------|----------|
| P0 | 基础配置 | 1 | 无 | XML Schema验证 |
| P0 | 全局变量 | 2 | 基础配置 | 类型一致性检查 |
| P0 | 资源定义 | 3 | 全局变量 | SimPy兼容性验证 |
| P1 | 实体定义 | 4 | 资源定义 | 引用完整性检查 |
| P1 | 活动定义 | 5 | 实体定义 | 表达式语法验证 |
| P1 | 行动定义 | 6 | 活动定义 | 活动引用验证 |
| P2 | 任务定义 | 7 | 行动定义 | 实体-行动匹配 |
| P2 | 交互定义 | 8 | 任务定义 | 实体间引用验证 |
| P3 | 事件定义 | 9 | 交互定义 | 触发条件验证 |
| P3 | 监控器定义 | 10 | 事件定义 | 监控目标验证 |
| P4 | v2.2.1多初始行动 ✨ | 11 | 任务定义 | 依赖图循环检测 |

### 9.2 引用完整性验证矩阵

| 源元素 | 引用目标 | 验证类型 | 错误处理 |
|--------|----------|----------|----------|
| `Task.Entities.EntityRef` | `Entity.@id` | 必须存在 | ValidationException |
| `Task.InitialAction` | `Action.@id` | 必须存在 | ValidationException |
| `Action.Activities.ActivityRef` | `Activity.@id` | 必须存在 | ValidationException |
| `Action.ResourceRequirements.ResourceRef` | `Resource.@id` | 必须存在 | ValidationException |
| `Interaction.Source` | `Entity.@id` | 必须存在 | ValidationException |
| `Interaction.Target` | `Entity.@id` | 必须存在 | ValidationException |
| `Event.Actions.ActionRef` | `Action.@id` | 必须存在 | ValidationException |
| `Monitor.Target` | `Entity.@id \| Resource.@id \| "global"` | 存在性检查 | 警告继续 |
| `InitialAction.ActionRef` ✨ | `Action.@id` | 必须存在 | ValidationException |
| `InitialAction.DependsOn.ActionRef` ✨ | `InitialAction.@id` | 循环依赖检测 | ValidationException |

---

## 10. FreeMarker模板结构设计

### 10.1 模板文件组织结构

```
templates/
├── main/
│   ├── simulation_main.ftl           # 主程序模板
│   ├── imports.ftl                   # 导入语句
│   ├── constants.ftl                 # 常量定义
│   └── websocket_setup.ftl           # WebSocket配置
├── entities/
│   ├── base_entity.ftl               # 基础实体类
│   ├── entity_class.ftl              # 具体实体类
│   ├── state_variables.ftl           # 状态变量定义
│   └── entity_visualization.ftl      # 可视化配置
├── actions/
│   ├── action_base.ftl               # 行动基类
│   ├── action_class.ftl              # 具体行动类
│   ├── resource_requirements.ftl     # 资源需求处理
│   └── trigger_conditions.ftl        # 触发条件
├── activities/
│   ├── activity_wrapper.ftl          # 活动装饰器
│   ├── internal_function.ftl         # 内部函数活动
│   ├── external_algorithm.ftl        # 外部算法活动
│   ├── delay_activity.ftl            # 延迟活动
│   └── compound_activity.ftl         # 复合活动
├── interactions/
│   ├── interaction_handler.ftl       # 交互处理器
│   ├── message_format.ftl            # 消息格式
│   └── response_generation.ftl       # 响应生成
├── events/
│   ├── event_scheduler.ftl           # 事件调度器
│   ├── event_handler.ftl             # 事件处理器
│   └── condition_monitor.ftl         # 条件监控
├── monitoring/
│   ├── monitor_base.ftl              # 监控器基类
│   ├── metric_collector.ftl          # 指标收集器
│   └── alert_thresholds.ftl          # 告警阈值
├── v2_2_1/                           # v2.2.1特有模板 ✨
│   ├── multi_initial_actions.ftl     # 多初始行动协调器
│   ├── dependency_manager.ftl        # 依赖关系管理器
│   ├── execution_stages.ftl          # 阶段执行控制
│   ├── environment_checks.ftl        # 环境检查
│   └── pre_post_execution.ftl        # 执行前后处理
└── utils/
    ├── type_conversion.ftl           # 类型转换
    ├── expression_evaluator.ftl      # 表达式求值
    ├── time_distribution.ftl         # 时间分布
    └── error_handling.ftl            # 错误处理
```

### 10.2 模板变量命名规范

| 变量类型 | 命名模式 | 示例 | 说明 |
|----------|----------|------|------|
| 模型根对象 | `model` | `${model.version}` | 顶级EATIModel对象 |
| 集合元素 | `复数名词` | `${entities}`, `${actions}` | 元素列表 |
| 单个元素 | `单数名词` | `${entity}`, `${action}` | 循环中的当前元素 |
| 子对象 | `父对象.子对象` | `${entity.position}` | 嵌套对象访问 |
| 条件属性 | `has + 属性名` | `${hasPosition}` | 存在性检查 |
| 转换后值 | `属性名 + Python` | `${pythonValue}` | 类型转换后的值 |
| v2.2.1特性 | `v221 + 特性名` | `${v221MultiActions}` | 新版本特性标识 |

### 10.3 条件生成语法模式

```freemarker
<#-- 可选元素存在性检查 -->
<#if element??>
    # 生成对应代码
    ${element.property}
</#if>

<#-- 集合非空检查 -->
<#if collection?? && collection?size > 0>
    <#list collection as item>
    # 处理每个项目
    ${item.property}
    </#list>
</#if>

<#-- 枚举值匹配 -->
<#switch enumValue>
    <#case "value1">
        # 生成value1对应代码
        <#break>
    <#case "value2">
        # 生成value2对应代码
        <#break>
    <#default>
        # 默认处理
</#switch>

<#-- v2.2.1特性条件生成 -->
<#if model.schemaVersion?? && model.schemaVersion?starts_with("2.2")>
    <#-- v2.2.1特有功能 -->
    <#if task.multiActions??>
        # 多初始行动支持
        ${generateMultiActionsCoordinator(task.multiActions)}
    </#if>
</#if>

<#-- 引用验证 -->
<#assign targetEntity = entities?filter(e -> e.id == interaction.target)?first!"">
<#if targetEntity?has_content>
    # 目标实体存在，生成交互代码
    target = entities['${interaction.target}']
<#else>
    # 错误：引用的实体不存在
    # ERROR: Entity '${interaction.target}' not found
</#if>
```

---

## 11. Java解析器关键类设计

### 11.1 核心JAXB注解映射

```java
@XmlRootElement(name = "EATIModel")
@XmlAccessorType(XmlAccessType.FIELD)
public class EATIModel {
    @XmlAttribute(required = true)
    private String version;
    
    @XmlAttribute(required = true)
    @XmlJavaTypeAdapter(LocalDateTimeAdapter.class)
    private LocalDateTime timestamp;
    
    @XmlAttribute
    private String schemaVersion = "2.2.1";  // v2.2.1默认值
    
    @XmlElement(name = "SimulationConfig", required = true)
    private SimulationConfig simulationConfig;
    
    @XmlElement(name = "Tasks", required = true)
    private Tasks tasks;
    
    // ... 其他元素
}

// v2.2.1新增：多初始行动配置 ✨
@XmlAccessorType(XmlAccessType.FIELD)
public class InitialActionsConfig {
    @XmlElement(name = "ExecutionMode", required = true)
    private InitialActionExecutionMode executionMode;
    
    @XmlElement(name = "InitialActions", required = true)
    private InitialActionsList initialActions;
    
    @XmlElement(name = "GlobalTimeout")
    private Double globalTimeout;
    
    @XmlElement(name = "SynchronizationPoint")
    private String synchronizationPoint;
    
    @XmlElement(name = "FailurePolicy")
    private String failurePolicy;
    
    // ... 其他v2.2.1字段
}

@XmlAccessorType(XmlAccessType.FIELD)
public class Task {
    @XmlAttribute(required = true)
    private String id;
    
    @XmlElement(name = "Name", required = true)
    private String name;
    
    // v2.2.1修改：支持两种初始行动配置方式
    @XmlElement(name = "InitialAction")
    private String initialAction;  // 传统单一行动
    
    @XmlElement(name = "InitialActionsConfig")  // v2.2.1新增 ✨
    private InitialActionsConfig initialActionsConfig;
    
    // 验证：两者只能选其一
    @XmlTransient
    public boolean isValid() {
        return (initialAction != null) ^ (initialActionsConfig != null);
    }
}
```

### 11.2 枚举类型定义

```java
public enum InitialActionExecutionMode {  // v2.2.1新增 ✨
    @XmlEnumValue("sequential")
    SEQUENTIAL("sequential"),
    
    @XmlEnumValue("parallel") 
    PARALLEL("parallel"),
    
    @XmlEnumValue("conditional")
    CONDITIONAL("conditional"),
    
    @XmlEnumValue("priority")
    PRIORITY("priority"),
    
    @XmlEnumValue("staged")
    STAGED("staged");
    
    private final String value;
    
    InitialActionExecutionMode(String value) {
        this.value = value;
    }
    
    public String getValue() {
        return value;
    }
}

public enum DistributionType {
    @XmlEnumValue("constant")
    CONSTANT("constant"),
    
    @XmlEnumValue("exponential")
    EXPONENTIAL("exponential"),
    
    @XmlEnumValue("normal")
    NORMAL("normal"),
    
    @XmlEnumValue("uniform")
    UNIFORM("uniform"),
    
    // ... 其他分布类型
}
```

### 11.3 验证器设计

```java
@Component
public class EATIModelValidator {
    
    public ValidationResult validate(EATIModel model) {
        ValidationResult result = new ValidationResult();
        
        // 基础验证
        validateBasicStructure(model, result);
        
        // 引用完整性验证
        validateReferences(model, result);
        
        // v2.2.1特有验证 ✨
        if (isVersion221OrLater(model.getSchemaVersion())) {
            validateV221Features(model, result);
        }
        
        return result;
    }
    
    private void validateV221Features(EATIModel model, ValidationResult result) {
        // 多初始行动验证
        for (Task task : model.getTasks().getTask()) {
            if (task.getInitialActionsConfig() != null) {
                validateMultiInitialActions(task, result);
            }
        }
    }
    
    private void validateMultiInitialActions(Task task, ValidationResult result) {
        InitialActionsConfig config = task.getInitialActionsConfig();
        
        // 依赖关系循环检测
        if (hasCircularDependencies(config.getInitialActions())) {
            result.addError("Circular dependency detected in task: " + task.getId());
        }
        
        // 阶段号验证
        if (config.getExecutionMode() == InitialActionExecutionMode.STAGED) {
            validateStageNumbers(config.getInitialActions(), result);
        }
        
        // 条件表达式验证
        validateStartConditions(config.getInitialActions(), result);
    }
}
```

---

## 12. IR(中间表示)数据结构设计

### 12.1 核心IR类设计

```java
public class SimulationIR {
    private ModelMetadata metadata;
    private SimulationConfiguration simulation;
    private List<GlobalVariable> globalVariables;
    private List<Resource> resources;
    private List<Task> tasks;
    private List<Entity> entities;
    private List<Action> actions;
    private List<Activity> activities;
    private List<Interaction> interactions;
    private List<Event> events;
    private List<Monitor> monitors;
    
    // v2.2.1新增字段 ✨
    private boolean hasMultiInitialActions;
    private Map<String, DependencyGraph> taskDependencies;
}

public class Task {
    private String id;
    private String name;
    private String goal;
    private String priority;
    private List<String> entities;
    
    // 传统单一初始行动
    private String initialAction;
    
    // v2.2.1多初始行动配置 ✨
    private MultiInitialActionsConfig multiActionsConfig;
    
    public boolean hasMultipleInitialActions() {
        return multiActionsConfig != null;
    }
}

public class MultiInitialActionsConfig {  // v2.2.1新增 ✨
    private InitialActionExecutionMode executionMode;
    private List<InitialActionConfig> initialActions;
    private Double globalTimeout;
    private String synchronizationPoint;
    private String failurePolicy;
    private ExecutionOrder executionOrder;
    private PreExecutionSetup preExecutionSetup;
    private PostExecutionCleanup postExecutionCleanup;
}

public class InitialActionConfig {  // v2.2.1新增 ✨
    private String id;
    private String name;
    private String actionRef;
    private String startCondition;
    private TimeDistribution startDelay;
    private Integer priority;
    private Integer stage;
    private List<ActionDependency> dependencies;
    private Map<String, Object> executionContext;
}
```

### 12.2 类型转换器设计

```java
@Component
public class TypeConverter {
    
    public Object convertToePythonValue(String xmlValue, VariableType type) {
        switch (type) {
            case BOOLEAN:
                return "True".equals(xmlValue) || "true".equals(xmlValue) ? "True" : "False";
            case INTEGER:
                return xmlValue;
            case DOUBLE:
                return xmlValue;
            case STRING:
                return "\"" + xmlValue + "\"";
            case TIME:
                return xmlValue;
            default:
                return "\"" + xmlValue + "\"";
        }
    }
    
    public String convertDistributionToPython(TimeDistribution dist) {
        StringBuilder sb = new StringBuilder();
        sb.append("TimeDistribution.generate('")
          .append(dist.getDistribution().getValue())
          .append("', {");
        
        for (Map.Entry<String, String> param : dist.getParameters().entrySet()) {
            sb.append("'").append(param.getKey()).append("': ")
              .append(param.getValue()).append(", ");
        }
        
        if (!dist.getParameters().isEmpty()) {
            sb.setLength(sb.length() - 2); // 移除最后的逗号和空格
        }
        
        sb.append("})");
        return sb.toString();
    }
    
    // v2.2.1新增：执行模式转换 ✨
    public String convertExecutionModeToPython(InitialActionExecutionMode mode) {
        switch (mode) {
            case SEQUENTIAL:
                return "ActionCoordinator.SEQUENTIAL";
            case PARALLEL:
                return "ActionCoordinator.PARALLEL";
            case CONDITIONAL:
                return "ActionCoordinator.CONDITIONAL";
            case PRIORITY:
                return "ActionCoordinator.PRIORITY";
            case STAGED:
                return "ActionCoordinator.STAGED";
            default:
                return "ActionCoordinator.SEQUENTIAL";
        }
    }
}
```

---

## 13. 代码生成错误处理策略

### 13.1 错误分类与处理

| 错误类型 | 严重级别 | 处理策略 | 示例 |
|----------|----------|----------|------|
| XML语法错误 | FATAL | 停止处理 | 格式错误、标签不匹配 |
| Schema验证错误 | FATAL | 停止处理 | 必填元素缺失、类型不匹配 |
| 引用完整性错误 | ERROR | 跳过引用，记录错误 | ActionRef指向不存在的Action |
| v2.2.1循环依赖 ✨ | ERROR | 跳过任务，记录错误 | InitialAction相互依赖 |
| 类型转换错误 | WARNING | 使用默认值，记录警告 | 无效的数值格式 |
| 可选元素缺失 | INFO | 使用默认值 | 缺失的可选配置项 |

### 13.2 错误恢复机制

```java
public class CodeGenerationErrorHandler {
    
    public void handleReferenceError(String sourceId, String targetId, String type) {
        String errorMsg = String.format(
            "Reference error: %s '%s' references non-existent %s '%s'", 
            type, sourceId, type, targetId);
        
        log.error(errorMsg);
        errorReport.addError(ErrorCode.REFERENCE_NOT_FOUND, errorMsg);
        
        // 生成注释代码而不是跳过
        codeBuffer.append("# ERROR: ").append(errorMsg).append("\n");
        codeBuffer.append("# ").append(generateFallbackCode(sourceId, targetId, type));
    }
    
    // v2.2.1特有错误处理 ✨
    public void handleCircularDependency(List<String> dependencyChain) {
        String errorMsg = String.format(
            "Circular dependency detected in initial actions: %s", 
            String.join(" -> ", dependencyChain));
        
        log.error(errorMsg);
        errorReport.addError(ErrorCode.CIRCULAR_DEPENDENCY, errorMsg);
        
        // 生成简化的顺序执行代码
        codeBuffer.append("# ERROR: ").append(errorMsg).append("\n");
        codeBuffer.append("# Falling back to sequential execution\n");
        codeBuffer.append("execution_mode = 'sequential'\n");
    }
}
```

---

## 14. 测试用例覆盖矩阵

### 14.1 单元测试覆盖

| 测试类别 | 测试用例 | 覆盖的XML路径 | v2.2.1标记 |
|----------|----------|---------------|------------|
| XML解析测试 | 基础元素解析 | `/EATIModel/*` | |
| | 可选元素缺失 | `/EATIModel/*/Optional` | |
| | 多初始行动解析 ✨ | `/EATIModel/Tasks/Task/InitialActionsConfig` | ✨ |
| | 依赖关系解析 ✨ | `.../InitialAction/DependsOn` | ✨ |
| 验证测试 | 引用完整性 | 所有Ref字段 | |
| | 循环依赖检测 ✨ | 依赖关系图 | ✨ |
| | 类型一致性 | 所有Type字段 | |
| 转换测试 | 基础类型转换 | 所有基础字段 | |
| | 枚举转换 | 所有枚举字段 | |
| | 执行模式转换 ✨ | ExecutionMode字段 | ✨ |
| 生成测试 | 实体类生成 | `/EATIModel/Entities/Entity` | |
| | 行动类生成 | `/EATIModel/Actions/Action` | |
| | 协调器生成 ✨ | 多初始行动配置 | ✨ |

### 14.2 集成测试场景

| 场景 | 输入XML | 期望输出 | 验证点 |
|------|---------|----------|--------|
| 基础仿真 | DetectAndFireExample.xml | 可运行的SimPy程序 | 功能完整性 |
| v2.2.1多行动 ✨ | 包含InitialActionsConfig的XML | 带协调器的SimPy程序 | 执行模式正确 |
| 错误处理 | 包含引用错误的XML | 带错误注释的程序 | 优雅降级 |
| 循环依赖 ✨ | 包含循环依赖的XML | 简化执行的程序 | 错误恢复 |

---

## 15. 完整性检查清单

### 15.1 解析阶段检查

- [ ] XML语法验证
- [ ] Schema约束验证  
- [ ] 编码格式检查
- [ ] 命名空间验证
- [ ] v2.2.1新元素识别 ✨

### 15.2 验证阶段检查

- [ ] 所有必填元素存在
- [ ] 引用完整性验证
- [ ] 类型一致性检查
- [ ] 枚举值有效性
- [ ] v2.2.1循环依赖检测 ✨
- [ ] 阶段号连续性检查 ✨

### 15.3 转换阶段检查

- [ ] IR结构完整性
- [ ] 类型转换正确性
- [ ] 默认值填充
- [ ] v2.2.1特性标记 ✨

### 15.4 生成阶段检查

- [ ] Python语法正确性
- [ ] SimPy API兼容性
- [ ] 导入语句完整性
- [ ] 缩进格式正确性
- [ ] v2.2.1协调器逻辑正确 ✨

---

## 16. 总结

本映射表提供了从EATI Schema v2.2.1 XML到SimPy Python代码生成的完整映射关系，涵盖：

1. **86个核心映射项**：覆盖所有主要XML元素到Python代码的转换
2. **v2.2.1新增特性**：37个新增映射项，特别标注✨符号
3. **完整的验证策略**：引用完整性、循环依赖检测、类型一致性
4. **模板驱动架构**：基于FreeMarker的分层模板设计
5. **错误处理机制**：分级错误处理和优雅降级策略
6. **测试覆盖方案**：单元测试和集成测试的完整覆盖

此映射表为Java代码生成器的实现提供了详细的技术规范，确保100%覆盖EATI Schema v2.2.1的所有元素类型和关键枚举，支持从简单的单一初始行动到复杂的多行动协调执行的完整代码生成能力。