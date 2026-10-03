// 슬라이드 p12-v11-newline — 보간 구멍 안의 switch 식, C# 11.0
using System;

class App
{
    static void Main()
    {
        foreach (int code in new[] { 200, 404, 503 })
        {
            Console.WriteLine($"{code}: {code switch
            {
                >= 200 and < 300 => "ok",
                404 => "not found",
                >= 500 => "server error",
                _ => "other",
            }}");
        }
    }
}
