// 슬라이드 p7-v6-dictinit-list — List 에 인덱스 초기화자, C# 6.0
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        List<int> a = new List<int> { 10, 20 };         // Add, Add
        List<int> b = new List<int>(a) { [0] = 1 };     // this[0] = 1
        Console.WriteLine(a.Count + " " + b[0] + " " + b.Count);
        try
        {
            List<int> c = new List<int>(5) { [0] = 10 };
        }
        catch (ArgumentOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
