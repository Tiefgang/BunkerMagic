#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArtnetWifi.h>
#include <FastLED.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi Settings
const char* ssid = "Tiefgang";
const char* password = "Wifi4Bunker";
String HOST_NAME = "http://bunker.light:8080";
String PATH_NAME = "/device_config"; // Fetch rows & columns from server

// LED Strip
constexpr int DATA_PIN = 12;
int rows = 0;         // Fetched from server
int columns = 0;      // Fetched from server
int num_leds = 0;     // Updated after fetching rows & columns
int num_channels = 0; // Updated after fetching rows & columns

CRGB* leds = nullptr;

// Artnet settings
ArtnetWifi artnet;
const int startUniverse = 0;
volatile bool sendFrame = false;
unsigned long lastPacketTime = 0;
const unsigned long timeoutThreshold = 30000; // Restart if no Art-Net for 30 sec

// WiFi Event Handler (Auto Restart on Disconnect)
void WiFiStationDisconnected(WiFiEvent_t event, WiFiEventInfo_t info) {
    Serial.println("WiFi disconnected! Restarting...");
    ESP.restart();
}

// Fetch configuration from the server
bool fetchConfiguration() {
    Serial.println("Fetching device configuration...");

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi not connected!");
        return false;
    }

    HTTPClient http;
    http.begin(HOST_NAME + PATH_NAME);
    
    int httpResponseCode = http.GET();
    if (httpResponseCode != 200) {
        Serial.print("HTTP GET request failed. Code: ");
        Serial.println(httpResponseCode);
        http.end();
        return false;
    }

    String payload = http.getString();
    http.end();

    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload);
    if (error) {
        Serial.println("JSON parsing failed!");
        return false;
    }

    if (!doc.containsKey("rows") || !doc.containsKey("columns")) {
        Serial.println("Invalid response format!");
        return false;
    }

    rows = doc["rows"];
    columns = doc["columns"];
    num_leds = rows * columns;
    num_channels = num_leds * 3;

    // Allocate LED memory dynamically
    if (leds) {
        delete[] leds;
    }
    leds = new CRGB[num_leds];

    Serial.print("Config received - Rows: ");
    Serial.print(rows);
    Serial.print(", Columns: ");
    Serial.println(columns);

    return true;
}

// Art-Net Packet Handler
void onDmxFrame(uint16_t universe, uint16_t length, uint8_t sequence, uint8_t* data) {
    lastPacketTime = millis(); // Reset timeout timer
    sendFrame = true;

    for (int i = 0; i < length / 3; i++) {
        int led = i + (1 + universe * (512 / 3 / columns) - 1) * columns;
        if (led < num_leds) {
            leds[led] = CRGB(data[i * 3], data[i * 3 + 1], data[i * 3 + 2]);
        }
    }
}

// Thread for Art-Net Processing
void artnetTask(void* parameter) {
    while (true) {
        artnet.read();

        if (millis() - lastPacketTime > timeoutThreshold) {
            Serial.println("No Art-Net received for too long, restarting...");
            ESP.restart();
        }

        vTaskDelay(1); // Yield to prevent watchdog timeout
    }
}

// Thread for LED Rendering
void ledTask(void* parameter) {
    while (true) {
        if (sendFrame) {
            FastLED.show();
            sendFrame = false;
        }

        vTaskDelay(10 / portTICK_PERIOD_MS); // Avoid excessive CPU usage
    }
}

// Setup function
void setup() {
    Serial.begin(115200);
    
    // Wi-Fi Connection
    WiFi.onEvent(WiFiStationDisconnected, WiFiEvent_t::ARDUINO_EVENT_WIFI_STA_DISCONNECTED);
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");

    int retry = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        if (++retry > 20) {
            Serial.println("\nWiFi failed! Restarting...");
            ESP.restart();
        }
    }

    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    // Fetch configuration
    if (!fetchConfiguration()) {
        Serial.println("Failed to fetch configuration, restarting...");
        ESP.restart();
    }

    // Initialize FastLED
    FastLED.addLeds<WS2812, DATA_PIN, GRB>(leds, num_leds);

    // Start Art-Net
    artnet.begin();
    artnet.setArtDmxCallback(onDmxFrame);

    Serial.println("Art-Net & LED system initialized!");

    // Create Tasks for Multi-threading
    xTaskCreatePinnedToCore(artnetTask, "ArtnetTask", 4096, NULL, 1, NULL, 0); // Core 0
    xTaskCreatePinnedToCore(ledTask, "LedTask", 4096, NULL, 1, NULL, 1);       // Core 1
}

// Main loop (unused since tasks handle everything)
void loop() {
    vTaskDelay(1000 / portTICK_PERIOD_MS);
}
