// 슬라이드 p14-v13-pm-err — params 로 쓸 수 없는 형식, C# 13
using System;
using System.Collections;
using System.Collections.Generic;

class NoAdd : IEnumerable<int>            // IEnumerable but no Add
{
    public IEnumerator<int> GetEnumerator() => null;
    IEnumerator IEnumerable.GetEnumerator() => null;
}

class Program
{
    static int Ok(params IReadOnlyList<int> xs) => xs.Count;
#if INT
    static int Bad1(params int x) => x;
#endif
#if NOADD
    static int Bad2(params NoAdd xs) => 0;
#endif
#if DICT
    static int Bad3(params IDictionary<int, int> xs) => xs.Count;
#endif
#if DEFAULT
    static int Bad4(params List<int> xs = null) => 0;
#endif

    static void Main() => Console.WriteLine(Ok(1, 2));
}
