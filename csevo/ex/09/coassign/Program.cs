// 슬라이드 p9-v8-coalesce — null 병합 할당 ??=, C# 8.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<int> numbers = null;
        int? i = null;

        numbers ??= new List<int>();
        numbers.Add(i ??= 17);
        numbers.Add(i ??= 20);

        Console.WriteLine(string.Join(" ", numbers));   // 17 17
        Console.WriteLine(i);                           // 17
    }
}
