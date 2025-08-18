# IR模型总体设计

## 1. 设计目标与原则

### 1.1 设计目标
- **完整性**：覆盖EATI Schema 2.2.1的所有86个核心映射关系和37个v2.2.1新特性
- **解耦性**：IR层独立于XML解析和代码生成，提供纯领域模型
- **类型安全**：强类型Java设计，编译时错误检查
- **扩展性**：支持未来新的EATI Schema版本和生成目标
- **性能**：支持大规模模型（1000+实体）的高效处理

### 1.2 设计原则
- **不可变性**：IR对象构建后不可修改，保证线程安全
- **验证集成**：每个IR对象支持自验证和关联验证
- **懒加载**：引用解析和复杂计算支持懒加载
- **缓存友好**：支持序列化和反序列化用于缓存
- **错误恢复**：提供优雅降级和错误恢复机制

## 2. IR架构层次

### 2.1 整体架构图
```
┌─────────────────────────────────────────┐
│              XML解析层                   │
│         (JAXB + 自定义解析器)            │
└─────────────────┬───────────────────────┘
                  │ XML → JAXB对象
                  ▼
┌─────────────────────────────────────────┐
│               IR层                       │
│  ┌─────────────────────────────────────┐ │
│  │        SimulationModel              │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │    核心业务模型                  │ │ │
│  │  │  • Entity, Action, Activity    │ │ │
│  │  │  • Task, Resource, Interaction │ │ │
│  │  │  • Event, Monitor              │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │    v2.2.1扩展模型              │ │ │
│  │  │  • MultiInitialActionsConfig   │ │ │
│  │  │  • DependencyGraph             │ │ │
│  │  │  • ExecutionStage              │ │ │
│  │  └─────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │    支撑模型                     │ │ │
│  │  │  • Expression, TimeDistribution│ │ │
│  │  │  • ValidationResult, Builder   │ │ │
│  │  │  • ReferenceManager            │ │ │
│  │  └─────────────────────────────────┘ │ │
│  └─────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │ IR → 模板变量
                  ▼
┌─────────────────────────────────────────┐
│             代码生成层                   │
│        (FreeMarker + 模板)              │
└─────────────────────────────────────────┘
```

### 2.2 核心包结构
```
com.eati.ir
├── model/                          # IR模型定义
│   ├── core/                       # 核心业务模型
│   │   ├── SimulationModel.java
│   │   ├── Entity.java
│   │   ├── Action.java
│   │   ├── Activity.java
│   │   ├── Task.java
│   │   ├── Resource.java
│   │   ├── Interaction.java
│   │   ├── Event.java
│   │   └── Monitor.java
│   ├── config/                     # 配置模型
│   │   ├── ModelMetadata.java
│   │   ├── SimulationConfiguration.java
│   │   ├── InterfaceConfiguration.java
│   │   └── CodeGenerationConfiguration.java
│   ├── v221/                       # v2.2.1扩展模型
│   │   ├── MultiInitialActionsConfig.java
│   │   ├── InitialActionConfig.java
│   │   ├── ActionDependency.java
│   │   ├── DependencyGraph.java
│   │   ├── ExecutionStage.java
│   │   └── PreExecutionSetup.java
│   ├── expression/                 # 表达式系统
│   │   ├── Expression.java
│   │   ├── TimeDistribution.java
│   │   ├── Condition.java
│   │   └── Parameter.java
│   └── types/                      # 类型系统
│       ├── IRVariableType.java
│       ├── IRDistributionType.java
│       ├── IRExecutionMode.java
│       └── IRResourceType.java
├── validation/                     # 验证框架
│   ├── IRValidator.java
│   ├── ValidationResult.java
│   ├── ValidationError.java
│   ├── ReferenceValidator.java
│   └── DependencyValidator.java
├── builder/                        # 构建器
│   ├── IRBuilder.java
│   ├── ModelBuilder.java
│   ├── V221FeatureBuilder.java
│   └── ExpressionBuilder.java
├── reference/                      # 引用管理
│   ├── ReferenceManager.java
│   ├── ReferenceResolver.java
│   └── CircularDependencyDetector.java
└── converter/                      # 类型转换
    ├── ValueConverter.java
    ├── TypeMapper.java
    └── PythonCodeGenerator.java
```

## 3. 根模型设计

### 3.1 SimulationModel - 根模型
```java
/**
 * EATI仿真模型的IR根表示
 * 包含完整的仿真定义和元数据
 */
@Immutable
@JsonSerializable
public final class SimulationModel {
    
    // 模型元数据
    private final ModelMetadata metadata;
    
    // 配置信息
    private final SimulationConfiguration simulationConfig;
    private final InterfaceConfiguration interfaceConfig;
    private final CodeGenerationConfiguration codeGenConfig;
    
    // 数据定义
    private final List<GlobalVariable> globalVariables;
    private final List<Resource> resources;
    
    // 行为定义
    private final List<Task> tasks;
    private final List<Entity> entities;
    private final List<Action> actions;
    private final List<Activity> activities;
    
    // 交互与事件
    private final List<Interaction> interactions;
    private final List<Event> events;
    
    // 监控
    private final List<Monitor> monitors;
    
    // v2.2.1特性支持
    private final boolean supportsMultiInitialActions;
    private final String schemaVersion;
    private final Map<String, DependencyGraph> taskDependencyGraphs;
    
    // 引用管理器（延迟初始化）
    @JsonIgnore
    private transient ReferenceManager referenceManager;
    
    // 构造器（Builder模式）
    private SimulationModel(Builder builder) {
        this.metadata = requireNonNull(builder.metadata, "metadata cannot be null");
        this.simulationConfig = requireNonNull(builder.simulationConfig, "simulationConfig cannot be null");
        this.interfaceConfig = builder.interfaceConfig;
        this.codeGenConfig = builder.codeGenConfig;
        this.globalVariables = ImmutableList.copyOf(builder.globalVariables);
        this.resources = ImmutableList.copyOf(builder.resources);
        this.tasks = ImmutableList.copyOf(builder.tasks);
        this.entities = ImmutableList.copyOf(builder.entities);
        this.actions = ImmutableList.copyOf(builder.actions);
        this.activities = ImmutableList.copyOf(builder.activities);
        this.interactions = ImmutableList.copyOf(builder.interactions);
        this.events = ImmutableList.copyOf(builder.events);
        this.monitors = ImmutableList.copyOf(builder.monitors);
        this.supportsMultiInitialActions = builder.supportsMultiInitialActions;
        this.schemaVersion = requireNonNull(builder.schemaVersion, "schemaVersion cannot be null");
        this.taskDependencyGraphs = ImmutableMap.copyOf(builder.taskDependencyGraphs);
    }
    
    /**
     * 获取引用管理器（懒加载）
     */
    public ReferenceManager getReferenceManager() {
        if (referenceManager == null) {
            synchronized (this) {
                if (referenceManager == null) {
                    referenceManager = new ReferenceManager(this);
                }
            }
        }
        return referenceManager;
    }
    
    /**
     * 验证整个模型
     */
    public ValidationResult validate() {
        return IRValidator.getInstance().validateModel(this);
    }
    
    /**
     * 检查是否支持v2.2.1特性
     */
    public boolean isVersion221OrLater() {
        return supportsMultiInitialActions || 
               schemaVersion.compareTo("2.2.1") >= 0;
    }
    
    /**
     * 查找指定类型的所有元素
     */
    public <T extends IRComponent> List<T> findAllOfType(Class<T> type) {
        return getReferenceManager().findAllOfType(type);
    }
    
    // Getter方法省略...
    
    /**
     * Builder模式构建器
     */
    public static class Builder {
        private ModelMetadata metadata;
        private SimulationConfiguration simulationConfig;
        private InterfaceConfiguration interfaceConfig;
        private CodeGenerationConfiguration codeGenConfig;
        private List<GlobalVariable> globalVariables = new ArrayList<>();
        private List<Resource> resources = new ArrayList<>();
        private List<Task> tasks = new ArrayList<>();
        private List<Entity> entities = new ArrayList<>();
        private List<Action> actions = new ArrayList<>();
        private List<Activity> activities = new ArrayList<>();
        private List<Interaction> interactions = new ArrayList<>();
        private List<Event> events = new ArrayList<>();
        private List<Monitor> monitors = new ArrayList<>();
        private boolean supportsMultiInitialActions = false;
        private String schemaVersion = "2.2.1";
        private Map<String, DependencyGraph> taskDependencyGraphs = new HashMap<>();
        
        public Builder metadata(ModelMetadata metadata) {
            this.metadata = metadata;
            return this;
        }
        
        public Builder simulationConfig(SimulationConfiguration config) {
            this.simulationConfig = config;
            return this;
        }
        
        public Builder addTask(Task task) {
            this.tasks.add(task);
            if (task.hasMultipleInitialActions()) {
                this.supportsMultiInitialActions = true;
            }
            return this;
        }
        
        public Builder addEntity(Entity entity) {
            this.entities.add(entity);
            return this;
        }
        
        public Builder addAction(Action action) {
            this.actions.add(action);
            return this;
        }
        
        // 其他builder方法...
        
        public SimulationModel build() {
            // 构建前验证
            validateBuilder();
            
            // 构建依赖图
            buildDependencyGraphs();
            
            return new SimulationModel(this);
        }
        
        private void validateBuilder() {
            if (metadata == null) {
                throw new IllegalStateException("metadata is required");
            }
            if (simulationConfig == null) {
                throw new IllegalStateException("simulationConfig is required");
            }
            if (tasks.isEmpty()) {
                throw new IllegalStateException("at least one task is required");
            }
            if (entities.isEmpty()) {
                throw new IllegalStateException("at least one entity is required");
            }
        }
        
        private void buildDependencyGraphs() {
            for (Task task : tasks) {
                if (task.hasMultipleInitialActions()) {
                    DependencyGraph graph = DependencyGraph.fromTask(task);
                    taskDependencyGraphs.put(task.getId(), graph);
                }
            }
        }
    }
}
```

### 3.2 基础IRComponent接口
```java
/**
 * 所有IR组件的基础接口
 */
public interface IRComponent {
    
    /**
     * 获取唯一标识符
     */
    String getId();
    
    /**
     * 获取名称
     */
    String getName();
    
    /**
     * 自验证
     */
    ValidationResult validate(ValidationContext context);
    
    /**
     * 获取所有引用的ID
     */
    Set<String> getReferencedIds();
    
    /**
     * 获取组件类型
     */
    IRComponentType getComponentType();
}

/**
 * IR组件类型枚举
 */
public enum IRComponentType {
    ENTITY,
    ACTION,
    ACTIVITY,
    TASK,
    RESOURCE,
    INTERACTION,
    EVENT,
    MONITOR,
    GLOBAL_VARIABLE
}
```

## 4. v2.2.1特性支持

### 4.1 多初始行动配置
```java
/**
 * v2.2.1新增：多初始行动配置
 * 支持任务的复杂启动逻辑
 */
@Immutable
public final class MultiInitialActionsConfig {
    
    private final InitialActionExecutionMode executionMode;
    private final List<InitialActionConfig> initialActions;
    private final Optional<Double> globalTimeout;
    private final Optional<String> synchronizationPoint;
    private final Optional<String> failurePolicy;
    private final Optional<ExecutionOrder> executionOrder;
    private final Optional<PreExecutionSetup> preExecutionSetup;
    private final Optional<PostExecutionCleanup> postExecutionCleanup;
    
    // 构造器和getter方法...
    
    /**
     * 构建依赖关系图
     */
    public DependencyGraph buildDependencyGraph() {
        return DependencyGraph.fromInitialActions(initialActions);
    }
    
    /**
     * 获取执行阶段列表（仅适用于STAGED模式）
     */
    public List<ExecutionStage> getExecutionStages() {
        if (executionMode != InitialActionExecutionMode.STAGED) {
            return Collections.emptyList();
        }
        
        return initialActions.stream()
            .collect(Collectors.groupingBy(InitialActionConfig::getStage))
            .entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .map(entry -> new ExecutionStage(entry.getKey(), entry.getValue()))
            .collect(Collectors.toList());
    }
    
    /**
     * 验证配置的有效性
     */
    @Override
    public ValidationResult validate(ValidationContext context) {
        ValidationResult result = new ValidationResult();
        
        // 检查执行模式与配置的一致性
        if (executionMode == InitialActionExecutionMode.STAGED) {
            validateStagedMode(result);
        }
        
        // 检查依赖关系
        DependencyGraph graph = buildDependencyGraph();
        if (graph.hasCircularDependency()) {
            result.addError("Circular dependency detected in initial actions");
        }
        
        // 检查超时设置
        if (globalTimeout.isPresent() && globalTimeout.get() <= 0) {
            result.addError("Global timeout must be positive");
        }
        
        return result;
    }
    
    private void validateStagedMode(ValidationResult result) {
        Set<Integer> stages = initialActions.stream()
            .map(InitialActionConfig::getStage)
            .collect(Collectors.toSet());
        
        // 检查阶段连续性
        List<Integer> sortedStages = stages.stream().sorted().collect(Collectors.toList());
        for (int i = 0; i < sortedStages.size() - 1; i++) {
            if (sortedStages.get(i + 1) - sortedStages.get(i) > 1) {
                result.addWarning("Stage numbers are not consecutive: " + sortedStages);
                break;
            }
        }
    }
}
```

### 4.2 初始行动配置
```java
/**
 * v2.2.1新增：单个初始行动配置
 */
@Immutable
public final class InitialActionConfig implements IRComponent {
    
    private final String id;
    private final String name;
    private final String actionRef;
    private final Optional<Expression> startCondition;
    private final Optional<TimeDistribution> startDelay;
    private final Integer priority;
    private final Integer stage;
    private final List<ActionDependency> dependencies;
    private final Map<String, Object> executionContext;
    
    // 构造器和基础方法...
    
    /**
     * 检查是否有依赖关系
     */
    public boolean hasDependencies() {
        return !dependencies.isEmpty();
    }
    
    /**
     * 获取所有依赖的行动ID
     */
    public Set<String> getDependentActionIds() {
        return dependencies.stream()
            .map(ActionDependency::getActionRef)
            .collect(Collectors.toSet());
    }
    
    /**
     * 检查是否有条件启动
     */
    public boolean hasStartCondition() {
        return startCondition.isPresent();
    }
    
    /**
     * 检查是否有启动延迟
     */
    public boolean hasStartDelay() {
        return startDelay.isPresent();
    }
    
    @Override
    public ValidationResult validate(ValidationContext context) {
        ValidationResult result = new ValidationResult();
        
        // 验证行动引用
        if (!context.getReferenceManager().actionExists(actionRef)) {
            result.addError("Referenced action does not exist: " + actionRef);
        }
        
        // 验证开始条件
        if (startCondition.isPresent()) {
            ValidationResult conditionResult = startCondition.get().validate(context);
            result.merge(conditionResult);
        }
        
        // 验证依赖关系
        for (ActionDependency dep : dependencies) {
            ValidationResult depResult = dep.validate(context);
            result.merge(depResult);
        }
        
        return result;
    }
    
    @Override
    public Set<String> getReferencedIds() {
        Set<String> refs = new HashSet<>();
        refs.add(actionRef);
        refs.addAll(getDependentActionIds());
        return refs;
    }
    
    @Override
    public IRComponentType getComponentType() {
        return IRComponentType.INITIAL_ACTION;
    }
}
```

## 5. 设计特性总结

### 5.1 类型安全特性
- **强类型枚举**：所有EATI枚举类型都有对应的Java枚举
- **泛型支持**：列表和映射使用泛型确保类型安全
- **空值安全**：使用Optional处理可选字段
- **编译时检查**：通过类型系统在编译时发现错误

### 5.2 不可变性设计
- **Final字段**：所有字段标记为final
- **Immutable注解**：使用Guava的@Immutable注解
- **防御性拷贝**：集合字段使用ImmutableList/ImmutableMap
- **Builder模式**：通过Builder模式创建不可变对象

### 5.3 验证集成
- **自验证接口**：每个组件实现validate方法
- **上下文验证**：验证时传递ValidationContext
- **错误聚合**：ValidationResult聚合所有错误和警告
- **增量验证**：支持部分模型的增量验证

### 5.4 性能优化
- **懒加载**：ReferenceManager和依赖图支持懒加载
- **缓存支持**：支持序列化用于缓存和持久化
- **内存优化**：使用弱引用处理大型模型
- **并发安全**：不可变设计天然支持并发访问

这个IR模型总体设计为整个代码生成器项目提供了稳定、高效、可扩展的中间表示层基础。