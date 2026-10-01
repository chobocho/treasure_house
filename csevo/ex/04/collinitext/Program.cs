// 슬라이드 p4-v3-collinit-ext — 확장 메서드 Add, C# 3.0
using System;
using System.Collections.Generic;

static class QueueExt
{
    public static void Add<T>(this Queue<T> q, T item)
    {
        q.Enqueue(item);
    }
}

class App
{
    static void Main()
    {
        Queue<string> q = new Queue<string> { "a", "b" };
        Console.WriteLine(q.Count + " " + q.Peek());
    }
}
