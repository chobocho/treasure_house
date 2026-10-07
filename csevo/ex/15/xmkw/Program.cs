// 슬라이드 p15-v14-xm-kw — extension 은 이제 문맥 키워드, C# 14
using System;

class @extension
{
    public int N;
    public @extension(object o) { N = 3; } // escaped: a constructor
#if CTOR
    public extension(int n) { N = n; }     // a constructor in C# 13
#elif RET
    public extension Self() => this;       // return type 'extension'
#endif
}

#if NAME
class Box<extension> { }                   // a type parameter name
#endif

class Program
{
    static void Main() => Console.WriteLine(new @extension(null).N);
}
