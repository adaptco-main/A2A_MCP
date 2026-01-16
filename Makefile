CXX := g++
CXXFLAGS := -I./include -std=c++17 -Wall -Wextra
LDFLAGS := 

SRC_DIRS := src src/engine src/agents src/safety
BUILD_DIR := build
BIN_DIR := bin

SRCS := $(wildcard src/*.cpp) $(wildcard src/engine/*.cpp) $(wildcard src/agents/*.cpp) $(wildcard src/safety/*.cpp)
OBJS := $(SRCS:%.cpp=$(BUILD_DIR)/%.o)
DEPS := $(OBJS:.o=.d)

TARGET := $(BIN_DIR)/ghost-void_engine

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(OBJS) -o $@ $(LDFLAGS)

$(BUILD_DIR)/%.o: %.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c $< -o $@

-include $(DEPS)

clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)

test:
	$(CXX) $(CXXFLAGS) tests/safety_test.cpp src/safety/SafetyLayer.cpp -o $(BIN_DIR)/safety_test
	./$(BIN_DIR)/safety_test
