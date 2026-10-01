// 슬라이드 p3-v2-generic-class — 제네릭 클래스 선언, C# 2.0
using System;

class MyStack<T>
{
    T[] items = new T[2];
    int count;

    public void Push(T item)
    {
        if (count == items.Length)
        {
            T[] bigger = new T[count * 2];
            Array.Copy(items, bigger, count);
            items = bigger;
        }
        items[count++] = item;
    }

    public T Pop()
    {
        return items[--count];
    }
}

class App
{
    static void Main()
    {
        MyStack<string> s = new MyStack<string>();
        s.Push("a");
        s.Push("b");
        s.Push("c");
        Console.WriteLine(s.Pop() + s.Pop() + s.Pop());
        MyStack<double> d = new MyStack<double>();
        d.Push(1.5);
        Console.WriteLine(d.Pop() * 2);
    }
}
