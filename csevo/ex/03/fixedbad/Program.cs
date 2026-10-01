// 슬라이드 p3-v2-fixed-rules — 고정 크기 버퍼의 규칙, C# 2.0
using System;

unsafe class InClass { public fixed int A[4]; }          // a class
unsafe struct OfString { public fixed string S[2]; }     // string
unsafe struct Shared { public static fixed int A[4]; }   // static
unsafe struct Empty { public fixed int A[0]; }           // length 0

class App
{
    static void Main() { }
}
