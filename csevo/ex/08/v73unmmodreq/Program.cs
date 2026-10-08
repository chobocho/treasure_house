// 슬라이드 p8-v7_3-unmanaged-meta — 제약 시그니처의 modreq, C# 7.3
using System;
using System.IO;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;

class App
{
    static void U<T>() where T : unmanaged { }
    static void S<T>() where T : struct { }
    static void Main()
    {
        var file = File.OpenRead(typeof(App).Assembly.Location);
        using (var pe = new PEReader(file))
        {
            MetadataReader md = pe.GetMetadataReader();
            foreach (var mh in md.MethodDefinitions)
            {
                var m = md.GetMethodDefinition(mh);
                string name = md.GetString(m.Name);
                if (name != "U" && name != "S") continue;
                var gh = m.GetGenericParameters()[0];
                var c = md.GetGenericParameter(gh).GetConstraints()[0];
                var t = md.GetGenericParameterConstraint(c).Type;
                Console.WriteLine(name + ": " + Show(md, t));
            }
        }
    }
    // 제약 형식이 TypeSpec 이면 시그니처를 읽어 modreq 를 꺼낸다
    static string Show(MetadataReader md, EntityHandle t)
    {
        if (t.Kind == HandleKind.TypeReference) return Name(md, t);
        var ts = md.GetTypeSpecification((TypeSpecificationHandle)t);
        BlobReader br = md.GetBlobReader(ts.Signature);
        br.ReadSignatureTypeCode();          // RequiredModifier
        string mod = Name(md, br.ReadTypeHandle());
        br.ReadSignatureTypeCode();          // 다음 형식 앞의 표지
        return "modreq(" + mod + ") " + Name(md, br.ReadTypeHandle());
    }
    static string Name(MetadataReader md, EntityHandle h)
    {
        var r = md.GetTypeReference((TypeReferenceHandle)h);
        return md.GetString(r.Namespace) + "." + md.GetString(r.Name);
    }
}
