// 슬라이드 p2-v1-covariance — 배열 공변성과 실행 시간 검사, C# 1.0
using System;

class App
{
    static void Fill(object[] items, object value)
    {
        for (int i = 0; i < items.Length; i++)
        {
            items[i] = value;                 // checked at run time
        }
        Console.WriteLine("filled with " + value);
    }

    static void Main()
    {
        string[] names = new string[2];
        object[] objs = names;                // string[] -> object[]
        Console.WriteLine(objs.GetType().Name);
        Fill(objs, "x");
        Fill(objs, 1);                        // int into a string[]
    }
}
