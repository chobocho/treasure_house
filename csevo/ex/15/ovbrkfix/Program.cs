// 슬라이드 p15-v14-brk-fix — 고쳐진 검사 둘, C# 14
using System;
using System.Threading.Tasks;

#if PTR
unsafe record struct R(int* P)       // CS8908 since VS 17.14
{
    public bool Equals(R other) => true;
    public override int GetHashCode() => 0;
}
#endif

class C
{
    public Enumerator GetAsyncEnumerator() => new Enumerator();

    public sealed class Enumerator
    {
        public int Current => 0;
        public ValueTask<bool> MoveNextAsync() => new(false);
#if OBS
        [Obsolete]                   // reported since VS 17.13
#endif
        public ValueTask DisposeAsync() => default;
    }
}

class Program
{
    static async Task Main()
    {
        await foreach (int i in new C()) Console.WriteLine(i);
        Console.WriteLine("done");
    }
}
