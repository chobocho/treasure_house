// 슬라이드 p12-v11-utf8-runtime — UTF-8 바이트를 받는 .NET API, C# 11.0
using System;
using System.Buffers;
using System.Text;
using System.Text.Json;
using System.Text.Unicode;

class App
{
    static void Main()
    {
        var buf = new ArrayBufferWriter<byte>();
        using (var w = new Utf8JsonWriter(buf))
        {
            w.WriteStartObject();
            w.WriteString("name"u8, "Ada"u8);  // UTF-8 in and out
            w.WriteNumber("cups"u8, 3);
            w.WriteEndObject();
        }
        ReadOnlySpan<byte> json = buf.WrittenSpan;
        Console.WriteLine(Encoding.UTF8.GetString(json));
        Console.WriteLine(Utf8.IsValid(json));
        var reader = new Utf8JsonReader(json);
        while (reader.Read())
            if (reader.TokenType == JsonTokenType.PropertyName
                && reader.ValueTextEquals("cups"u8))
            {
                reader.Read();
                Console.WriteLine("cups = " + reader.GetInt32());
            }
    }
}
