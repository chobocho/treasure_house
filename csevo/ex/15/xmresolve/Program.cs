// 슬라이드 p15-v14-xm-resolve — 인스턴스 멤버가 먼저다, C# 14
using System;
using System.Collections.Generic;

static class Ext
{
    extension(string s)
    {
        public int Length => -1;                  // never chosen
        public string ToUpper() => "ext";         // never chosen
        public string Shout => s.ToUpper() + "!";
    }

    extension(List<int> list)
    {
        public int Count(int x) => list.FindAll(v => v == x).Count;
    }
}

class Program
{
    static void Main()
    {
        string s = "abc";
        Console.WriteLine(s.Length + " " + s.ToUpper() + " " + s.Shout);
        Console.WriteLine(Ext.get_Length(s) + " " + Ext.ToUpper(s));
        var list = new List<int> { 1, 2, 2 };
        Console.WriteLine(list.Count + " " + list.Count(2));
    }
}
