// 슬라이드 p4-v3-collinit-gate — 컬렉션 초기화자, C# 3.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        List<int> digits = new List<int> { 0, 1, 2, 3 };

        List<int> same = new List<int>();     // what it stands for
        same.Add(0); same.Add(1); same.Add(2); same.Add(3);
        Console.WriteLine(digits.Count + " " + same.Count);
    }
}
