#ifndef ZIMGPLUSPLUS_HPP_
#define ZIMGPLUSPLUS_HPP_

#include "zimg.h"

#ifndef ZIMGXX_NAMESPACE
  #define ZIMGXX_NAMESPACE zimgxx
#endif

/**
 * C++ bindings for zlib API.
 *
 * None of the structures and functions described in this header should be
 * considered part of the API or ABI. Users must not pass objects defined in
 * this header across application or library boundaries.
 *
 * To avoid symbol conflicts on certain platforms, applications in which
 * multiple zlib users may be resident should define {@p ZIMGXX_NAMESPACE} as
 * an application-specific value.
 *
 * {@p ZIMGXX_NAMESPACE} must not be defined as "zimg".
 */
namespace ZIMGXX_NAMESPACE {

struct zerror {
	zimg_error_code_e code;
	char msg[64];

	zerror()
	{
		code = zimg_get_last_error(msg, sizeof(msg));
	}
};

struct zimage_buffer_const : zimg_image_buffer_const {
	zimage_buffer_const() : zimg_image_buffer_const()
	{
		version = ZIMG_API_VERSION;
	}

	const void *line_at(unsigned i, unsigned p = 0) const
	{
		return static_cast<const char *>(data(p)) + static_cast<ptrdiff_t>(i & mask(p)) * stride(p);
	}

	const void *data(unsigned p = 0) const
	{
		return plane[p].data;
	}

	const void *&data(unsigned p = 0)
	{
		return plane[p].data;
	}

	ptrdiff_t stride(unsigned p = 0) const
	{
		return plane[p].stride;
	}

	ptrdiff_t &stride(unsigned p = 0)
	{
		return plane[p].stride;
	}

	unsigned mask(unsigned p = 0) const
	{
		return plane[p].mask;
	}

	unsigned &mask(unsigned p = 0)
	{
		return plane[p].mask;
	}
};

struct zimage_buffer : zimg_image_buffer {
	zimage_buffer() : zimg_image_buffer()
	{
		version = ZIMG_API_VERSION;
	}

	const zimage_buffer_const as_const() const
	{
		union {
			zimage_buffer m;
			zimage_buffer_const c;
		} u = { *this };

		return u.c;
	}

	void *line_at(unsigned i, unsigned p = 0) const
	{
		return static_cast<char *>(data(p)) + static_cast<ptrdiff_t>(i & mask(p)) * stride(p);
	}

	void *data(unsigned p = 0) const
	{
		return plane[p].data;
	}

	void *&data(unsigned p = 0)
	{
		return plane[p].data;
	}

	ptrdiff_t stride(unsigned p = 0) const
	{
		return plane[p].stride;
	}

	ptrdiff_t &stride(unsigned p = 0)
	{
		return plane[p].stride;
	}

	unsigned mask(unsigned p = 0) const
	{
		return plane[p].mask;
	}

	unsigned &mask(unsigned p = 0)
	{
		return plane[p].mask;
	}
};

struct zimage_format : zimg_image_format {
	zimage_format()
	{
		zimg_image_format_default(this, ZIMG_API_VERSION);
	}
};

struct zfilter_graph_builder_params : zimg_graph_builder_params {
	zfilter_graph_builder_params()
	{
		zimg_graph_builder_params_default(this, ZIMG_API_VERSION);
	}
};

class FilterGraph {
	zimg_filter_graph *m_graph;

	FilterGraph(const FilterGraph &);

	FilterGraph &operator=(const FilterGraph &);

	void check(zimg_error_code_e err) const
	{
		if (err)
			throw zerror();
	}
public:
	explicit FilterGraph(zimg_filter_graph *graph) : m_graph(graph)
	{
	}

	~FilterGraph()
	{
		zimg_filter_graph_free(m_graph);
	}

#if __cplusplus >= 201103L || (defined(_MSC_VER) && _MSC_VER >= 1600)
	FilterGraph() : m_graph()
	{
	}

	FilterGraph(FilterGraph &&other) : m_graph(other.m_graph)
	{
		other.m_graph = 0;
	}

	FilterGraph &operator=(FilterGraph &&other)
	{
		if (this != &other) {
			zimg_filter_graph_free(m_graph);
			m_graph = other.m_graph;
			other.m_graph = 0;
		}

		return *this;
	}

	explicit operator bool() const
	{
		return m_graph != 0;
	}
#endif

	size_t get_tmp_size() const
	{
		size_t ret;
		check(zimg_filter_graph_get_tmp_size(m_graph, &ret));
		return ret;
	}

	unsigned get_input_buffering() const
	{
		unsigned ret;
		check(zimg_filter_graph_get_input_buffering(m_graph, &ret));
		return ret;
	}

	unsigned get_output_buffering() const
	{
		unsigned ret;
		check(zimg_filter_graph_get_output_buffering(m_graph, &ret));
		return ret;
	}

	void process(const zimg_image_buffer_const &src, const zimg_image_buffer &dst, void *tmp,
	             zimg_filter_graph_callback unpack_cb = 0, void *unpack_user = 0,
	             zimg_filter_graph_callback pack_cb = 0, void *pack_user = 0) const
	{
		check(zimg_filter_graph_process(m_graph, &src, &dst, tmp, unpack_cb, unpack_user, pack_cb, pack_user));
	}

#if __cplusplus >= 201103L || (defined(_MSC_VER) && _MSC_VER >= 1600)
	static FilterGraph build(const zimg_image_format &src_format, const zimg_image_format &dst_format, const zimg_graph_builder_params *params = 0)
	{
		zimg_filter_graph *graph;

		if (!(graph = zimg_filter_graph_build(&src_format, &dst_format, params)))
			throw zerror();

		return FilterGraph(graph);
	}
#else
	static zimg_filter_graph *build(const zimg_image_format &src_format, const zimg_image_format &dst_format, const zimg_graph_builder_params *params = 0)
	{
		zimg_filter_graph *graph;

		if (!(graph = zimg_filter_graph_build(&src_format, &dst_format, params)))
			throw zerror();

		return graph;
	}
#endif
};

} // namespace zimgxx

#endif // ZIMGPLUSPLUS_HPP_
