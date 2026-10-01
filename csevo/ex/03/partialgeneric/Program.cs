// 슬라이드 p3-v2-partial-generic — 제네릭 조각이 어긋나면, C# 2.0
using System;

partial class Box<T> where T : struct { }   // other constraint
partial class Pair<A, B> { }                // other names

class App
{
    static void Main() { }
}
