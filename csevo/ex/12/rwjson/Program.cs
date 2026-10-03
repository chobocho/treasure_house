// 슬라이드 p12-v11-raw-json — $$ 로 만든 JSON 을 파서에 넣는다, C# 11.0
using System;
using System.Text.Json;

class App
{
    static string Order(int id, string item, double price) => $$"""
        {
          "id": {{id}},
          "lines": [ { "item": "{{item}}", "price": {{price:F2}} } ],
          "note": "braces { } and JSON escapes \" pass through"
        }
        """;

    static void Main()
    {
        string json = Order(7, "tea", 3.5);
        using JsonDocument doc = JsonDocument.Parse(json);
        JsonElement root = doc.RootElement;
        Console.WriteLine(root.GetProperty("id").GetInt32());
        JsonElement line = root.GetProperty("lines")[0];
        Console.WriteLine(line.GetProperty("price").GetDouble());
        Console.WriteLine(root.GetProperty("note").GetString());
    }
}
