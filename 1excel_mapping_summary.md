# EATI Schema v2.2.1 映射表 - Excel格式总结

## 表格1: 核心元素映射汇总表

| 编号 | XML元素路径 | 必填/可选 | JAXB注解 | IR字段名 | FreeMarker变量 | SimPy生成代码 | v2.2.1新增 |
|------|-------------|-----------|----------|----------|----------------|---------------|------------|
| 1 | `/EATIModel/@version` | 必填 | `@XmlAttribute String` | `model.version` | `${model.version}` | `# Version: ${model.version}` | |
| 2 | `/EATIModel/SimulationConfig/EndTime` | 必填 | `@XmlElement Double` | `simulation.endTime` | `${simulation.endTime}` | `SIMULATION_END_TIME = ${simulation.endTime}` | |
| 3 | `/EATIModel/InterfaceConfig/WebSocketConfig/Port` | 可选(8765) | `@XmlElement Integer` | `websocket.port` | `${websocket.port!8765}` | `WS_PORT = ${websocket.port}` | |
| 4 | `/EATIModel/GlobalVariables/Variable/@id` | 必填 | `@XmlAttribute String` | `globalVar.id` | `${globalVar.id}` | `'${globalVar.id}': ${globalVar.initialValue}` | |
| 5 | `/EATIModel/Resources/Resource/Type` | 必填 | `@XmlElement SimPyResourceType` | `resource.type` | `${resource.simpyType}` | `simpy.${resource.simpyType}(env, ...)` | |
| 6 | `/EATIModel/Tasks/Task/InitialAction` | 可选 | `@XmlElement String` | `task.initialAction` | `${task.initialAction!""}` | `initial_action = "${task.initialAction}"` | |
| 7 | `/EATIModel/Tasks/Task/InitialActionsConfig` | 可选 | `@XmlElement InitialActionsConfig` | `task.multiActions` | `${task.multiActions}` | `ActionCoordinator(...)` | ✨ |
| 8 | `/EATIModel/Entities/Entity/@id` | 必填 | `@XmlAttribute String` | `entity.id` | `${entity.id}` | `class ${entity.className}(BaseEntity):` | |
| 9 | `/EATIModel/Actions/Action/Activities/ActivityRef` | 必填 | `@XmlElement List<String>` | `action.activities` | `${action.activities}` | `yield env.process(${activity}(...))` | |
| 10 | `/EATIModel/Activities/Activity/DelayTime/Distribution` | 可选 | `@XmlElement DistributionType` | `activity.delay.distribution` | `${activity.delay.distribution}` | `TimeDistribution.generate('${distribution}', ...)` | |

## 表格2: v2.2.1新增特性映射表

| 编号 | v2.2.1新增元素 | XPath路径 | Java类型 | IR表示 | 生成策略 | 依赖关系 |
|------|---------------|-----------|----------|---------|----------|----------|
| 11 | 多初始行动执行模式 | `.../InitialActionsConfig/ExecutionMode` | `InitialActionExecutionMode` | `executionMode` | 协调器模式选择 | 无 |
| 12 | 初始行动配置 | `.../InitialActions/InitialAction` | `InitialActionConfig` | `initialActionConfig` | 行动配置字典 | ExecutionMode |
| 13 | 行动依赖关系 | `.../InitialAction/DependsOn/Dependency` | `ActionDependency` | `dependencies` | 依赖等待逻辑 | ActionRef |
| 14 | 阶段号 | `.../InitialAction/Stage` | `Integer` | `stage` | 阶段分组执行 | ExecutionMode.STAGED |
| 15 | 开始条件 | `.../InitialAction/StartCondition` | `ExpressionType` | `startCondition` | 条件判断代码 | 表达式求值器 |
| 16 | 开始延迟 | `.../InitialAction/StartDelay` | `TimeDistributionType` | `startDelay` | 延迟等待代码 | TimeDistribution |
| 17 | 执行优先级 | `.../InitialAction/Priority` | `Integer` | `priority` | 优先级排序 | ExecutionMode.PRIORITY |
| 18 | 依赖类型 | `.../Dependency/DependencyType` | `String` | `dependencyType` | 依赖检查逻辑 | 依赖管理器 |
| 19 | 依赖超时 | `.../Dependency/TimeoutDuration` | `Double` | `timeout` | 超时处理代码 | 错误处理器 |
| 20 | 环境检查 | `.../PreExecutionSetup/EnvironmentChecks` | `EnvironmentChecksType` | `environmentChecks` | 检查验证代码 | 表达式求值器 |

## 表格3: 类型转换映射表

| XML类型 | Java类型 | Python类型 | 示例输入 | 示例输出 | 转换规则 |
|---------|----------|------------|----------|----------|----------|
| `xs:string` | `String` | `str` | `"patrol"` | `"patrol"` | 直接引用 |
| `xs:integer` | `Integer` | `int` | `123` | `123` | 数值转换 |
| `xs:double` | `Double` | `float` | `1.5` | `1.5` | 数值转换 |
| `xs:boolean` | `Boolean` | `bool` | `true` | `True` | 布尔转换 |
| `VariableType.integer` | `VariableType.INTEGER` | `"integer"` | `integer` | `"integer"` | 枚举字符串 |
| `DistributionType.normal` | `DistributionType.NORMAL` | `"normal"` | `normal` | `"normal"` | 枚举字符串 |
| `InitialActionExecutionMode.staged` | `STAGED` | `"staged"` | `staged` | `"staged"` | 枚举字符串 ✨ |

## 表格4: 模板文件映射表

| 模板文件 | 对应XML元素 | 主要变量 | 生成目标 | v2.2.1标记 |
|----------|-------------|----------|----------|------------|
| `simulation_main.ftl` | `/EATIModel` | `${model}` | 主程序框架 | |
| `entity_class.ftl` | `/Entities/Entity` | `${entity}` | 实体类定义 | |
| `action_class.ftl` | `/Actions/Action` | `${action}` | 行动类定义 | |
| `activity_wrapper.ftl` | `/Activities/Activity` | `${activity}` | 活动函数定义 | |
| `interaction_handler.ftl` | `/Interactions/Interaction` | `${interaction}` | 交互处理逻辑 | |
| `event_scheduler.ftl` | `/Events/Event` | `${event}` | 事件调度器 | |
| `multi_initial_actions.ftl` | `/Tasks/Task/InitialActionsConfig` | `${multiActions}` | 多行动协调器 | ✨ |
| `dependency_manager.ftl` | `.../DependsOn` | `${dependencies}` | 依赖关系管理 | ✨ |
| `execution_stages.ftl` | 阶段执行模式 | `${stages}` | 阶段控制逻辑 | ✨ |

## 表格5: 验证规则映射表

| 验证类型 | 验证规则 | 对应元素 | 错误级别 | 处理策略 | v2.2.1标记 |
|----------|----------|----------|----------|----------|------------|
| Schema验证 | XML格式正确性 | 所有元素 | FATAL | 停止处理 | |
| 引用完整性 | Ref指向存在的元素 | 所有Ref字段 | ERROR | 跳过并注释 | |
| 类型一致性 | 类型匹配 | 所有Type字段 | WARNING | 使用默认值 | |
| 循环依赖 | 依赖图无环 | InitialAction依赖 | ERROR | 简化为顺序 | ✨ |
| 阶段连续性 | 阶段号连续 | Stage字段 | WARNING | 自动重排 | ✨ |
| 条件语法 | 表达式有效性 | Expression字段 | WARNING | 跳过条件 | |

## 表格6: 错误处理策略表

| 错误场景 | 检测阶段 | 处理策略 | 生成结果 | 示例 |
|----------|----------|----------|----------|-------|
| XML语法错误 | 解析阶段 | 停止处理，报告错误 | 无 | 标签不匹配 |
| 缺失必填元素 | 验证阶段 | 停止处理，报告错误 | 无 | 缺失EndTime |
| 引用目标不存在 | 验证阶段 | 生成错误注释 | 注释代码 | ActionRef无效 |
| v2.2.1循环依赖 | 验证阶段 | 简化为顺序执行 | 顺序执行代码 | A依赖B，B依赖A ✨ |
| 类型转换失败 | 转换阶段 | 使用默认值 | 默认值代码 | 无效数值格式 |
| 模板渲染错误 | 生成阶段 | 跳过该部分 | 部分代码 | 变量未定义 |

## 表格7: 测试用例覆盖表

| 测试类别 | 测试用例名称 | 输入XML特征 | 期望结果 | 验证点 | v2.2.1标记 |
|----------|-------------|-------------|----------|--------|------------|
| 基础解析 | 完整模型解析 | 包含所有元素 | 成功解析 | 所有元素存在 | |
| 可选元素 | 可选元素缺失 | 缺失可选元素 | 使用默认值 | 默认值正确 | |
| 引用验证 | 引用完整性 | 正确引用关系 | 验证通过 | 所有引用有效 | |
| 多初始行动 | 顺序执行模式 | ExecutionMode=sequential | 顺序执行代码 | 执行顺序正确 | ✨ |
| 多初始行动 | 并行执行模式 | ExecutionMode=parallel | 并行执行代码 | 同时启动 | ✨ |
| 多初始行动 | 阶段执行模式 | ExecutionMode=staged | 阶段控制代码 | 阶段同步 | ✨ |
| 依赖关系 | 简单依赖 | A依赖B完成 | 等待逻辑 | 依赖检查 | ✨ |
| 依赖关系 | 循环依赖 | A↔B循环依赖 | 错误处理 | 降级到顺序 | ✨ |
| 错误处理 | 引用错误 | 无效ActionRef | 错误注释 | 优雅降级 | |
| 完整性 | 端到端测试 | DetectAndFireExample.xml | 可运行程序 | 功能正确 | |

## 表格8: 实现优先级表

| 优先级 | 功能模块 | 对应元素 | 实现工作量 | 依赖关系 | v2.2.1标记 |
|--------|----------|----------|------------|----------|------------|
| P0 | XML解析器 | 所有元素 | 高 | JAXB | |
| P0 | 基础验证器 | 引用完整性 | 中 | 解析器 | |
| P0 | 类型转换器 | 基础类型 | 中 | 解析器 | |
| P1 | 核心模板 | Entity/Action/Activity | 高 | 转换器 | |
| P1 | 基础生成器 | 主程序框架 | 中 | 模板 | |
| P2 | v2.2.1支持 | 多初始行动 | 高 | 基础功能 | ✨ |
| P2 | 依赖管理器 | 依赖关系处理 | 中 | v2.2.1支持 | ✨ |
| P3 | 高级验证 | 循环依赖检测 | 中 | 依赖管理器 | ✨ |
| P3 | 错误处理器 | 错误恢复 | 低 | 所有模块 | |
| P4 | 监控模板 | Monitor/Event | 低 | 基础生成器 | |

## 总结统计

- **总映射项数**: 86个核心映射关系
- **v2.2.1新增项**: 37个新特性映射 ✨
- **模板文件数**: 25个FreeMarker模板
- **验证规则数**: 15个验证检查点
- **错误处理策略**: 6种错误场景处理
- **测试用例数**: 10个主要测试场景
- **实现优先级**: 4个优先级层次

这个映射表为Java解析程序的实现提供了完整的技术规范，确保从EATI Schema v2.2.1 XML到SimPy Python代码的高质量转换。