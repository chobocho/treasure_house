// 슬라이드 p3-v2-static-refused — static 클래스의 선언 규칙, C# 2.0
using System;

static class Util
{
    public int Cube(int x) { return x * x * x; }   // instance member
}

class Derived : Util { }                           // inherit

static class Named : ICloneable { }                // interface

class App
{
    static void Use(Util u) { }                    // parameter type
    static void Main() { }
}
