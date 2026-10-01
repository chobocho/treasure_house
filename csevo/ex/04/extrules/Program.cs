// 슬라이드 p4-v3-ext-rules — 확장 메서드를 둘 수 있는 곳, C# 3.0
using System;

class NotStatic
{
    public static int A(this int n) { return n; }
}

static class Generic<T>
{
    public static int B(this int n) { return n; }
}

static class Outer
{
    static class Nested
    {
        public static int C(this int n) { return n; }
    }
    public static int D(int n, this int m) { return n; }
}

class App
{
    static void Main() { Console.WriteLine(1); }
}
