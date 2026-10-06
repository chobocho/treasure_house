// 슬라이드 p13-v12-ce-cinit — 컬렉션 초기화자 형식이 대상일 때, C# 12
using System;
using System.Collections;
using System.Collections.Generic;

class Log : IEnumerable
{
    readonly List<string> lines = [];
    public void Add(string s)
    {
        lines.Add(s);
        Console.WriteLine("Add " + s);
    }
    public IEnumerator GetEnumerator() => lines.GetEnumerator();
}

class NoEnum
{
    public void Add(int x) { }
}

class Program
{
    static void Main()
    {
        Log log = ["a", "b"];          // new Log() + Add + Add
        HashSet<int> set = [3, 1, 3];  // Add ignores the duplicate
        Console.WriteLine(set.Count);
#if BAD
        NoEnum n = [1];
#endif
    }
}
